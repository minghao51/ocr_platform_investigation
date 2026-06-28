import aiosqlite
import json
from typing import Optional, Dict, Any
from database.pool import connect
from database.crud._shared import loads_if_json


async def enqueue_job(
    job_id: int,
    task_type: str,
    file_path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    async with connect() as db:
        await db.execute(
            """
            INSERT INTO job_queue (job_id, task_type, file_path, payload, status, updated_at)
            VALUES (?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
            ON CONFLICT(job_id) DO UPDATE SET
                task_type = excluded.task_type,
                file_path = excluded.file_path,
                payload = excluded.payload,
                status = 'pending',
                worker_id = NULL,
                locked_at = NULL,
                last_error = NULL,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                job_id,
                task_type,
                file_path,
                json.dumps(payload or {}),
            ),
        )
        await db.commit()


async def claim_next_queued_job(worker_id: str) -> Optional[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            UPDATE job_queue
            SET status = 'processing',
                attempts = attempts + 1,
                worker_id = ?,
                locked_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = (
                SELECT id
                FROM job_queue
                WHERE status = 'pending'
                  AND datetime(COALESCE(run_after, CURRENT_TIMESTAMP)) <= datetime('now')
                ORDER BY created_at ASC
                LIMIT 1
            )
            RETURNING *
            """,
            (worker_id,),
        )
        row = await cursor.fetchone()
        await db.commit()
        if not row:
            return None

        item = dict(row)
        item["payload"] = loads_if_json(item.get("payload")) or {}
        return item


async def mark_queue_job_completed(job_id: int) -> None:
    async with connect() as db:
        await db.execute(
            """
            UPDATE job_queue
            SET status = 'completed',
                worker_id = NULL,
                locked_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
            """,
            (job_id,),
        )
        await db.commit()


async def mark_queue_job_failed(job_id: int, error_message: str) -> None:
    async with connect() as db:
        await db.execute(
            """
            UPDATE job_queue
            SET status = 'failed',
                worker_id = NULL,
                locked_at = NULL,
                last_error = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
            """,
            (error_message[:2000], job_id),
        )
        await db.commit()


async def recover_inflight_queue_jobs() -> int:
    async with connect() as db:
        await db.execute("BEGIN IMMEDIATE")
        try:
            cursor = await db.execute(
                "SELECT job_id FROM job_queue WHERE status = 'processing'"
            )
            stuck_ids = [row[0] for row in await cursor.fetchall()]
            if not stuck_ids:
                await db.commit()
                return 0

            placeholders = ",".join("?" for _ in stuck_ids)
            await db.execute(
                f"""
                UPDATE processing_jobs
                SET status = 'pending',
                    error_message = NULL
                WHERE id IN ({placeholders}) AND status = 'processing'
                """,
                stuck_ids,
            )
            await db.execute(
                """
                UPDATE job_queue
                SET status = 'pending',
                    worker_id = NULL,
                    locked_at = NULL,
                    last_error = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE status = 'processing'
                """
            )
            await db.commit()
            return len(stuck_ids)
        except Exception:
            await db.rollback()
            raise

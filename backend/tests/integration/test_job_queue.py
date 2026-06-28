import asyncio
from pathlib import Path

import pytest

from database import crud
from database.migrations import run_migrations
from database.pool import connect


@pytest.fixture
def queue_db_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "job-queue.db"
    monkeypatch.setattr("paths.get_db_path", lambda: db_path)
    monkeypatch.setattr("database.pool.get_db_path", lambda: db_path)
    monkeypatch.setattr("database.migrations.get_db_path", lambda: db_path)
    monkeypatch.setattr("dependencies._get_cached_db_path", lambda: db_path)

    asyncio.run(run_migrations())
    return db_path


async def _fetch_queue_row(job_id: int) -> dict | None:
    async with connect() as db:
        cursor = await db.execute(
            """
            SELECT job_id, status, worker_id, locked_at, last_error, attempts, payload
            FROM job_queue
            WHERE job_id = ?
            """,
            (job_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


def test_queue_claim_and_failure_updates_state(queue_db_env):
    _ = queue_db_env
    job_id = asyncio.run(
        crud.create_job(
            file_name="queue-sample.pdf",
            file_type="pdf",
            provider="gemini",
            model="gemini-2.5-flash",
            schema_id=None,
            schema_name="Custom",
            processing_method="vision",
        )
    )
    asyncio.run(
        crud.enqueue_job(
            job_id=job_id,
            task_type="processing",
            file_path="/tmp/queue-sample.pdf",
            payload={"step": "start"},
        )
    )

    item = asyncio.run(crud.claim_next_queued_job("worker-1"))
    assert item is not None
    assert item["job_id"] == job_id
    assert item["status"] == "processing"
    assert item["payload"] == {"step": "start"}

    asyncio.run(crud.mark_queue_job_failed(job_id, "Queue worker failed: boom"))
    row = asyncio.run(_fetch_queue_row(job_id))

    assert row is not None
    assert row["status"] == "failed"
    assert row["worker_id"] is None
    assert row["locked_at"] is None
    assert row["last_error"] == "Queue worker failed: boom"
    assert row["attempts"] == 1


def test_recover_inflight_queue_jobs_resets_processing_rows(queue_db_env):
    _ = queue_db_env
    job_id = asyncio.run(
        crud.create_job(
            file_name="recover-sample.pdf",
            file_type="pdf",
            provider="gemini",
            model="gemini-2.5-flash",
            schema_id=None,
            schema_name="Custom",
            processing_method="vision",
        )
    )
    asyncio.run(
        crud.enqueue_job(
            job_id=job_id,
            task_type="processing",
            file_path="/tmp/recover-sample.pdf",
            payload={"step": "resume"},
        )
    )

    async def _mark_processing() -> None:
        async with connect() as db:
            await db.execute(
                """
                UPDATE job_queue
                SET status = 'processing',
                    worker_id = 'worker-9',
                    locked_at = CURRENT_TIMESTAMP,
                    last_error = 'stale error'
                WHERE job_id = ?
                """,
                (job_id,),
            )
            await db.execute(
                "UPDATE processing_jobs SET status = 'processing' WHERE id = ?",
                (job_id,),
            )
            await db.commit()

    asyncio.run(_mark_processing())

    recovered = asyncio.run(crud.recover_inflight_queue_jobs())
    assert recovered == 1

    row = asyncio.run(_fetch_queue_row(job_id))
    job = asyncio.run(crud.get_job(job_id))

    assert row is not None
    assert row["status"] == "pending"
    assert row["worker_id"] is None
    assert row["locked_at"] is None
    assert row["last_error"] is None
    assert job is not None
    assert job["status"] == "pending"

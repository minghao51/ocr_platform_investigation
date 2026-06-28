import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from database.pool import connect


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


async def create_job(
    file_name: str,
    file_type: str,
    provider: str,
    model: str,
    schema_id: Optional[int],
    schema_name: Optional[str],
    processing_method: str = "vision",
    document_type: Optional[str] = None,
    user_id: Optional[int] = None,
    guest_token: Optional[str] = None,
) -> int:
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO processing_jobs
               (file_name, file_type, provider, model, schema_id, schema_name, status, processing_method, document_type, user_id, guest_token)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                file_name,
                file_type,
                provider,
                model,
                schema_id,
                schema_name,
                "pending",
                processing_method,
                document_type,
                user_id,
                guest_token,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def update_job_status(
    job_id: int,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    processing_time: Optional[float] = None,
    usage: Optional[Dict[str, Any]] = None,
    correction_status: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    prompt_tokens = None
    completion_tokens = None
    total_tokens = None
    estimated_cost = None

    if usage:
        prompt_tokens = usage.get("prompt_tokens") or usage.get("promptTokenCount")
        completion_tokens = usage.get("completion_tokens") or usage.get(
            "candidatesTokenCount"
        )
        total_tokens = usage.get("total_tokens") or usage.get("totalTokenCount")

    async with connect() as db:
        db.row_factory = aiosqlite.Row

        if prompt_tokens is not None and completion_tokens is not None:
            from services.pricing import calculate_cost

            cursor = await db.execute(
                "SELECT model FROM processing_jobs WHERE id = ?", (job_id,)
            )
            row = await cursor.fetchone()
            if row:
                estimated_cost = calculate_cost(
                    row["model"], prompt_tokens, completion_tokens
                )

        completed_at = (
            datetime.now().isoformat() if status in ("success", "error") else None
        )

        if status == "success":
            await db.execute(
                """UPDATE processing_jobs
                   SET status = ?, result = ?, processing_time_seconds = ?,
                       prompt_tokens = ?, completion_tokens = ?, total_tokens = ?,
                       estimated_cost = ?, completed_at = ?,
                       correction_status = COALESCE(?, correction_status)
                   WHERE id = ?""",
                (
                    status,
                    json.dumps(result) if result else None,
                    processing_time,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    estimated_cost,
                    completed_at,
                    correction_status,
                    job_id,
                ),
            )
        elif status == "error":
            await db.execute(
                """UPDATE processing_jobs
                   SET status = ?, error_message = ?, processing_time_seconds = ?,
                       prompt_tokens = ?, completion_tokens = ?, total_tokens = ?,
                       estimated_cost = ?, completed_at = ?,
                       correction_status = COALESCE(?, correction_status)
                   WHERE id = ?""",
                (
                    status,
                    error_message,
                    processing_time,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    estimated_cost,
                    completed_at,
                    correction_status,
                    job_id,
                ),
            )
        else:
            await db.execute(
                """UPDATE processing_jobs
                   SET status = ?, processing_time_seconds = ?,
                       prompt_tokens = ?, completion_tokens = ?, total_tokens = ?,
                       estimated_cost = ?,
                       correction_status = COALESCE(?, correction_status)
                   WHERE id = ?""",
                (
                    status,
                    processing_time,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    estimated_cost,
                    correction_status,
                    job_id,
                ),
            )
        await db.commit()

        cursor = await db.execute(
            "SELECT * FROM processing_jobs WHERE id = ?", (job_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM processing_jobs WHERE id = ?", (job_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def list_jobs(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row

        query = "SELECT * FROM processing_jobs WHERE 1=1"
        params: List[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(offset)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def delete_job(job_id: int) -> bool:
    async with connect() as db:
        cursor = await db.execute("DELETE FROM processing_jobs WHERE id = ?", (job_id,))
        await db.commit()
        return cursor.rowcount > 0


async def count_jobs(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    user_id: Optional[int] = None,
) -> int:
    async with connect() as db:
        query = "SELECT COUNT(*) FROM processing_jobs WHERE 1=1"
        params: List[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        cursor = await db.execute(query, params)
        row = await cursor.fetchone()
        return row[0] if row else 0


async def update_job_metadata(job_id: int, metadata: Dict[str, Any]) -> None:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        await db.execute("BEGIN IMMEDIATE")
        try:
            cursor = await db.execute(
                "SELECT metadata FROM processing_jobs WHERE id = ?", (job_id,)
            )
            row = await cursor.fetchone()
            merged_metadata = metadata
            if row and row["metadata"]:
                try:
                    existing = json.loads(row["metadata"])
                    if isinstance(existing, dict):
                        merged_metadata = {**existing, **metadata}
                except (json.JSONDecodeError, TypeError):
                    pass

            await db.execute(
                "UPDATE processing_jobs SET metadata = ? WHERE id = ?",
                (json.dumps(merged_metadata), job_id),
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def update_quality_info(
    job_id: int,
    quality_score: Optional[float] = None,
    quality_checks: Optional[Dict[str, Any]] = None,
    preprocessing_applied: Optional[list[str]] = None,
) -> None:
    sets: List[str] = []
    params: List[Any] = []

    if quality_score is not None:
        sets.append("quality_score = ?")
        params.append(quality_score)
    if quality_checks is not None:
        sets.append("quality_checks = ?")
        params.append(json.dumps(quality_checks, default=_json_default))
    if preprocessing_applied is not None:
        sets.append("preprocessing_applied = ?")
        params.append(json.dumps(preprocessing_applied, default=_json_default))

    if not sets:
        return

    params.append(job_id)
    sql = f"UPDATE processing_jobs SET {', '.join(sets)} WHERE id = ?"
    async with connect() as db:
        await db.execute(sql, params)
        await db.commit()


async def create_uploaded_file(
    file_id: str,
    original_filename: str,
    file_extension: str,
    file_path: str,
    file_size: int,
    content_type: str,
    user_id: Optional[int] = None,
    guest_token: Optional[str] = None,
) -> int:
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO uploaded_files
               (file_id, original_filename, file_extension, file_path, file_size, content_type, user_id, guest_token)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                file_id,
                original_filename,
                file_extension,
                file_path,
                file_size,
                content_type,
                user_id,
                guest_token,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_uploaded_file(file_id: str) -> Optional[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM uploaded_files WHERE file_id = ?", (file_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

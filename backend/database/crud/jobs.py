import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from database.pool import connect
from database.validators import validate_update_columns


def _build_update_sql(table: str, fields: dict, where_col: str = "id") -> tuple[str, tuple]:
    validate_update_columns(set(fields.keys()))
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    return (
        f"UPDATE {table} SET {set_clause} WHERE {where_col} = ?",
        tuple(fields.values()),
    )


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
        completion_tokens = usage.get("completion_tokens") or usage.get("candidatesTokenCount")
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
                estimated_cost = calculate_cost(row["model"], prompt_tokens, completion_tokens)

        completed_at = datetime.now().isoformat() if status in ("success", "error") else None
        update_fields = {
            "status": status,
            "processing_time_seconds": processing_time,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": estimated_cost,
        }
        if correction_status is not None:
            update_fields["correction_status"] = correction_status
        if status == "success":
            update_fields["result"] = json.dumps(result) if result else None
            update_fields["completed_at"] = completed_at
        elif status == "error":
            update_fields["error_message"] = error_message
            update_fields["completed_at"] = completed_at

        validate_update_columns(set(update_fields.keys()))

        sql, params_tuple = _build_update_sql("processing_jobs", update_fields)
        await db.execute(sql, (*params_tuple, job_id))
        await db.commit()

        cursor = await db.execute("SELECT * FROM processing_jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM processing_jobs WHERE id = ?", (job_id,))
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
        await db.execute("DELETE FROM processing_jobs WHERE id = ?", (job_id,))
        await db.commit()
        return True


async def update_job_metadata(job_id: int, metadata: Dict[str, Any]) -> None:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
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


async def update_quality_info(
    job_id: int,
    quality_score: Optional[float] = None,
    quality_checks: Optional[Dict[str, Any]] = None,
    preprocessing_applied: Optional[list[str]] = None,
) -> None:
    update_fields = {}

    if quality_score is not None:
        update_fields["quality_score"] = quality_score
    if quality_checks is not None:
        update_fields["quality_checks"] = json.dumps(quality_checks)
    if preprocessing_applied is not None:
        update_fields["preprocessing_applied"] = json.dumps(preprocessing_applied)

    if not update_fields:
        return

    sql, params_tuple = _build_update_sql("processing_jobs", update_fields)
    async with connect() as db:
        await db.execute(sql, (*params_tuple, job_id))
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

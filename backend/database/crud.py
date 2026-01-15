import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path("./data/ocr_platform.db")

async def create_schema(
    name: str,
    definition: Dict[str, Any],
    description: Optional[str] = None,
    is_template: bool = False
) -> int:
    """Create a new schema"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO schemas (name, description, definition, is_template)
               VALUES (?, ?, ?, ?)""",
            (name, description, json.dumps(definition), is_template)
        )
        await db.commit()
        return cursor.lastrowid

async def get_schema(schema_id: int) -> Optional[Dict[str, Any]]:
    """Get schema by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM schemas WHERE id = ?",
            (schema_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

async def list_schemas(
    is_template: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """List all schemas"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if is_template is not None:
            cursor = await db.execute(
                "SELECT * FROM schemas WHERE is_template = ? ORDER BY name",
                (is_template,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM schemas ORDER BY name"
            )

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def create_job(
    file_name: str,
    file_type: str,
    provider: str,
    model: str,
    schema_id: Optional[int],
    schema_name: Optional[str]
) -> int:
    """Create a new processing job"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO processing_jobs
               (file_name, file_type, provider, model, schema_id, schema_name, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (file_name, file_type, provider, model, schema_id, schema_name, "pending")
        )
        await db.commit()
        return cursor.lastrowid

async def update_job_status(
    job_id: int,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    processing_time: Optional[float] = None
) -> None:
    """Update job status"""
    async with aiosqlite.connect(DB_PATH) as db:
        if status == "success":
            completed_at = datetime.now().isoformat()
            await db.execute(
                """UPDATE processing_jobs
                   SET status = ?, result = ?, completed_at = ?, processing_time_seconds = ?
                   WHERE id = ?""",
                (status, json.dumps(result) if result else None, completed_at, processing_time, job_id)
            )
        elif status == "error":
            completed_at = datetime.now().isoformat()
            await db.execute(
                """UPDATE processing_jobs
                   SET status = ?, error_message = ?, completed_at = ?
                   WHERE id = ?""",
                (status, error_message, completed_at, job_id)
            )
        else:
            await db.execute(
                "UPDATE processing_jobs SET status = ? WHERE id = ?",
                (status, job_id)
            )
        await db.commit()

async def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Get job by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM processing_jobs WHERE id = ?",
            (job_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

async def list_jobs(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """List jobs with optional filters"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        query = "SELECT * FROM processing_jobs WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if provider:
            query += " AND provider = ?"
            params.append(provider)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def delete_job(job_id: int) -> bool:
    """Delete a job"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM processing_jobs WHERE id = ?", (job_id,))
        await db.commit()
        return True

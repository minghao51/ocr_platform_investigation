import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from database.pool import connect

DB_PATH = Path("./data/ocr_platform.db")


# ============================================================================
# User CRUD Operations
# ============================================================================

async def create_user(username: str, hashed_password: str, is_admin: bool = True, is_limited: bool = False) -> int:
    """Create a new user."""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO users (username, hashed_password, is_admin, is_limited)
               VALUES (?, ?, ?, ?)""",
            (username, hashed_password, is_admin, is_limited)
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def list_users() -> List[Dict[str, Any]]:
    """List all users (excluding password hashes)."""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, username, is_admin, created_at
               FROM users
               ORDER BY created_at DESC"""
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# ============================================================================
# Original CRUD Operations (will be updated with user_id)
# ============================================================================

async def create_schema(
    name: str,
    definition: Dict[str, Any],
    description: Optional[str] = None,
    is_template: bool = False
) -> int:
    """Create a new schema"""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO schemas (name, description, definition, is_template)
               VALUES (?, ?, ?, ?)""",
            (name, description, json.dumps(definition), is_template)
        )
        await db.commit()
        return cursor.lastrowid

async def get_schema(schema_id: int) -> Optional[Dict[str, Any]]:
    """Get schema by ID"""
    async with connect() as db:
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
    async with connect() as db:
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
    schema_name: Optional[str],
    processing_method: str = "vision",
    user_id: Optional[int] = None
) -> int:
    """Create a new processing job"""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO processing_jobs
               (file_name, file_type, provider, model, schema_id, schema_name, status, processing_method, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (file_name, file_type, provider, model, schema_id, schema_name, "pending", processing_method, user_id)
        )
        await db.commit()
        return cursor.lastrowid

async def update_job_status(
    job_id: int,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    processing_time: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Update job status and return the updated job data.

    Returns the updated job data, or None if job not found.
    """
    async with connect() as db:
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
                   SET status = ?, error_message = ?, completed_at = ?, processing_time_seconds = ?
                   WHERE id = ?""",
                (status, error_message, completed_at, processing_time, job_id)
            )
        else:
            await db.execute(
                "UPDATE processing_jobs SET status = ? WHERE id = ?",
                (status, job_id)
            )
        await db.commit()

        # Fetch and return the updated job
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM processing_jobs WHERE id = ?",
            (job_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

async def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Get job by ID"""
    async with connect() as db:
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
    user_id: Optional[int] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """List jobs with optional filters"""
    async with connect() as db:
        db.row_factory = aiosqlite.Row

        query = "SELECT * FROM processing_jobs WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if provider:
            query += " AND provider = ?"
            params.append(provider)

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def delete_job(job_id: int) -> bool:
    """Delete a job"""
    async with connect() as db:
        await db.execute("DELETE FROM processing_jobs WHERE id = ?", (job_id,))
        await db.commit()
        return True


async def update_job_metadata(job_id: int, metadata: Dict[str, Any]) -> None:
    """Update job metadata (stored in result field as JSON)"""
    async with connect() as db:
        # Get current job data
        cursor = await db.execute("SELECT result FROM processing_jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
        if not row:
            return

        # Merge with existing result if any
        try:
            existing_result = json.loads(row[0]) if row[0] else {}
        except (json.JSONDecodeError, TypeError):
            existing_result = {}

        existing_result["metadata"] = metadata

        # Update the result field with the merged data
        await db.execute(
            "UPDATE processing_jobs SET result = ? WHERE id = ?",
            (json.dumps(existing_result), job_id)
        )
        await db.commit()

async def create_uploaded_file(
    file_id: str,
    original_filename: str,
    file_extension: str,
    file_path: str,
    file_size: int,
    content_type: str
) -> int:
    """Create a new uploaded file record"""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO uploaded_files
               (file_id, original_filename, file_extension, file_path, file_size, content_type)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (file_id, original_filename, file_extension, file_path, file_size, content_type)
        )
        await db.commit()
        return cursor.lastrowid

async def get_uploaded_file(file_id: str) -> Optional[Dict[str, Any]]:
    """Get uploaded file by file_id"""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM uploaded_files WHERE file_id = ?",
            (file_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from database.pool import connect


# ============================================================================
# User CRUD Operations
# ============================================================================


async def create_user(
    username: str, hashed_password: str, is_admin: bool = True, is_limited: bool = False
) -> int:
    """Create a new user."""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO users (username, hashed_password, is_admin, is_limited)
               VALUES (?, ?, ?, ?)""",
            (username, hashed_password, is_admin, is_limited),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def list_users() -> List[Dict[str, Any]]:
    """List all users (excluding password hashes)."""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, username, is_admin, is_limited, daily_requests, last_request_date, created_at
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
    is_template: bool = False,
) -> int:
    """Create a new schema"""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO schemas (name, description, definition, is_template)
               VALUES (?, ?, ?, ?)""",
            (name, description, json.dumps(definition), is_template),
        )
        await db.commit()
        return cursor.lastrowid


async def get_schema(schema_id: int) -> Optional[Dict[str, Any]]:
    """Get schema by ID"""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM schemas WHERE id = ?", (schema_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def list_schemas(is_template: Optional[bool] = None) -> List[Dict[str, Any]]:
    """List all schemas"""
    async with connect() as db:
        db.row_factory = aiosqlite.Row

        if is_template is not None:
            cursor = await db.execute(
                "SELECT * FROM schemas WHERE is_template = ? ORDER BY name",
                (is_template,),
            )
        else:
            cursor = await db.execute("SELECT * FROM schemas ORDER BY name")

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
    user_id: Optional[int] = None,
) -> int:
    """Create a new processing job"""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO processing_jobs
               (file_name, file_type, provider, model, schema_id, schema_name, status, processing_method, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                file_name,
                file_type,
                provider,
                model,
                schema_id,
                schema_name,
                "pending",
                processing_method,
                user_id,
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
) -> Optional[Dict[str, Any]]:
    """
    Update job status and return the updated job data.

    Returns the updated job data, or None if job not found.
    """
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

        if prompt_tokens is not None and completion_tokens is not None:
            from services.pricing import calculate_cost

            async with connect() as db_cost:
                db_cost.row_factory = aiosqlite.Row
                cursor = await db_cost.execute(
                    "SELECT model FROM processing_jobs WHERE id = ?", (job_id,)
                )
                row = await cursor.fetchone()
                if row:
                    estimated_cost = calculate_cost(
                        row["model"], prompt_tokens, completion_tokens
                    )

    async with connect() as db:
        completed_at = (
            datetime.now().isoformat() if status in ("success", "error") else None
        )
        update_fields = {
            "status": status,
            "processing_time_seconds": processing_time,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": estimated_cost,
        }
        if status == "success":
            update_fields["result"] = json.dumps(result) if result else None
            update_fields["completed_at"] = completed_at
        elif status == "error":
            update_fields["error_message"] = error_message
            update_fields["completed_at"] = completed_at

        await db.execute(
            f"""UPDATE processing_jobs
               SET {", ".join(f"{k} = ?" for k in update_fields)}
               WHERE id = ?""",
            (*update_fields.values(), job_id),
        )
        await db.commit()

        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM processing_jobs WHERE id = ?", (job_id,)
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
) -> List[Dict[str, Any]]:
    """List jobs with optional filters"""
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
    """Update job metadata JSON without mutating the extracted result payload."""
    async with connect() as db:
        await db.execute(
            "UPDATE processing_jobs SET metadata = ? WHERE id = ?",
            (json.dumps(metadata), job_id),
        )
        await db.commit()


async def create_uploaded_file(
    file_id: str,
    original_filename: str,
    file_extension: str,
    file_path: str,
    file_size: int,
    content_type: str,
    user_id: Optional[int] = None,
) -> int:
    """Create a new uploaded file record"""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO uploaded_files
               (file_id, original_filename, file_extension, file_path, file_size, content_type, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                file_id,
                original_filename,
                file_extension,
                file_path,
                file_size,
                content_type,
                user_id,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_uploaded_file(file_id: str) -> Optional[Dict[str, Any]]:
    """Get uploaded file by file_id"""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM uploaded_files WHERE file_id = ?", (file_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


# ============================================================================
# Benchmark CRUD Operations
# ============================================================================


async def create_benchmark_run(
    dataset: str,
    provider: str,
    model: str,
    sample_count: int,
) -> int:
    """Create a new benchmark run record"""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO benchmark_runs
               (dataset, provider, model, sample_count)
               VALUES (?, ?, ?, ?)""",
            (dataset, provider, model, sample_count),
        )
        await db.commit()
        return cursor.lastrowid


async def update_benchmark_run(
    run_id: int,
    overall_accuracy: Optional[float] = None,
    avg_latency: Optional[float] = None,
    total_cost: Optional[float] = None,
    total_prompt_tokens: Optional[int] = None,
    total_completion_tokens: Optional[int] = None,
) -> None:
    """Update benchmark run with aggregated results"""
    async with connect() as db:
        await db.execute(
            """UPDATE benchmark_runs
               SET overall_accuracy = ?, avg_latency = ?, total_cost = ?,
                   total_prompt_tokens = ?, total_completion_tokens = ?,
                   completed_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (
                overall_accuracy,
                avg_latency,
                total_cost,
                total_prompt_tokens,
                total_completion_tokens,
                run_id,
            ),
        )
        await db.commit()


async def add_benchmark_result(
    run_id: int,
    sample_index: int,
    file_path: Optional[str] = None,
    accuracy_score: Optional[float] = None,
    latency: Optional[float] = None,
    cost: Optional[float] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    expected_json: Optional[str] = None,
    actual_json: Optional[str] = None,
    field_scores: Optional[str] = None,
    error_message: Optional[str] = None,
) -> int:
    """Add a single benchmark result"""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO benchmark_results
               (run_id, sample_index, file_path, accuracy_score, latency, cost,
                prompt_tokens, completion_tokens, expected_json, actual_json,
                field_scores, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                sample_index,
                file_path,
                accuracy_score,
                latency,
                cost,
                prompt_tokens,
                completion_tokens,
                expected_json,
                actual_json,
                field_scores,
                error_message,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def list_benchmark_runs(
    limit: int = 50,
    dataset: Optional[str] = None,
    provider: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List benchmark runs, most recent first, with optional filters."""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        where_clauses = []
        params: List[Any] = []

        if dataset:
            where_clauses.append("br.dataset = ?")
            params.append(dataset)
        if provider:
            where_clauses.append("br.provider = ?")
            params.append(provider)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        params.append(limit)
        cursor = await db.execute(
            f"""
            SELECT
                br.*,
                stats.success_rate AS success_rate
            FROM benchmark_runs br
            LEFT JOIN (
                SELECT
                    run_id,
                    CAST(SUM(CASE WHEN accuracy_score >= 0.5 THEN 1 ELSE 0 END) AS REAL)
                        / NULLIF(COUNT(*), 0) AS success_rate
                FROM benchmark_results
                GROUP BY run_id
            ) stats ON stats.run_id = br.id
            {where_sql}
            ORDER BY br.started_at DESC
            LIMIT ?
            """,
            params,
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_benchmark_run(run_id: int) -> Optional[Dict[str, Any]]:
    """Get a benchmark run by ID."""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                br.*,
                stats.success_rate AS success_rate
            FROM benchmark_runs br
            LEFT JOIN (
                SELECT
                    run_id,
                    CAST(SUM(CASE WHEN accuracy_score >= 0.5 THEN 1 ELSE 0 END) AS REAL)
                        / NULLIF(COUNT(*), 0) AS success_rate
                FROM benchmark_results
                GROUP BY run_id
            ) stats ON stats.run_id = br.id
            WHERE br.id = ?
            """,
            (run_id,),
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_benchmark_results(run_id: int) -> List[Dict[str, Any]]:
    """Get all results for a benchmark run"""
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM benchmark_results WHERE run_id = ? ORDER BY sample_index",
            (run_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

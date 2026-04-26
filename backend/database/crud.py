import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from database.pool import connect
from database.validators import validate_update_columns


def _loads_if_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


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
    document_type: Optional[str] = None,
    user_id: Optional[int] = None,
    guest_token: Optional[str] = None,
) -> int:
    """Create a new processing job"""
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

        await db.execute(
            f"""UPDATE processing_jobs
               SET {", ".join(f"{k} = ?" for k in update_fields)}
               WHERE id = ?""",
            (*update_fields.values(), job_id),
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
    offset: int = 0,
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

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(offset)

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
    """Update quality gate information for a job."""
    update_fields = {}

    if quality_score is not None:
        update_fields["quality_score"] = quality_score
    if quality_checks is not None:
        update_fields["quality_checks"] = json.dumps(quality_checks)
    if preprocessing_applied is not None:
        update_fields["preprocessing_applied"] = json.dumps(preprocessing_applied)

    if not update_fields:
        return

    # Validate all column names before SQL interpolation
    validate_update_columns(set(update_fields.keys()))

    async with connect() as db:
        await db.execute(
            f"""UPDATE processing_jobs
               SET {", ".join(f"{k} = ?" for k in update_fields)}
               WHERE id = ?""",
            (*update_fields.values(), job_id),
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
    guest_token: Optional[str] = None,
) -> int:
    """Create a new uploaded file record"""
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
    processing_method: str = "vision",
) -> int:
    """Create a new benchmark run record"""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO benchmark_runs
               (dataset, provider, model, sample_count, processing_method)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset, provider, model, sample_count, processing_method),
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
    peak_memory_mb: Optional[float] = None,
) -> int:
    """Add a single benchmark result"""
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO benchmark_results
               (run_id, sample_index, file_path, accuracy_score, latency, cost,
                prompt_tokens, completion_tokens, expected_json, actual_json,
                field_scores, error_message, peak_memory_mb)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                peak_memory_mb,
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
            """SELECT id, run_id, sample_index, file_path, accuracy_score, latency, cost,
                      prompt_tokens, completion_tokens, expected_json, actual_json,
                      field_scores, error_message, peak_memory_mb
               FROM benchmark_results WHERE run_id = ? ORDER BY sample_index""",
            (run_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# ============================================================================
# Phase 2/3 CRUD Operations
# ============================================================================


async def create_schema_suggestion(
    file_ids: List[str],
    provider: str,
    model: str,
    schema_definition: Dict[str, Any],
    field_descriptions: Dict[str, str],
    rationale: str,
    confidence: float,
    document_type: Optional[str] = None,
    draft_name: Optional[str] = None,
    created_by_user_id: Optional[int] = None,
) -> int:
    async with connect() as db:
        cursor = await db.execute(
            """
            INSERT INTO schema_suggestions (
                file_ids, provider, model, document_type, draft_name,
                schema_definition, field_descriptions, rationale, confidence, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                json.dumps(file_ids),
                provider,
                model,
                document_type,
                draft_name,
                json.dumps(schema_definition),
                json.dumps(field_descriptions),
                rationale,
                confidence,
                created_by_user_id,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_schema_suggestion(suggestion_id: int) -> Optional[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM schema_suggestions WHERE id = ?",
            (suggestion_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        result["file_ids"] = _loads_if_json(result.get("file_ids")) or []
        result["schema_definition"] = (
            _loads_if_json(result.get("schema_definition")) or {}
        )
        result["field_descriptions"] = (
            _loads_if_json(result.get("field_descriptions")) or {}
        )
        return result


async def list_schema_suggestions(
    created_by_user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        if created_by_user_id is None:
            cursor = await db.execute(
                "SELECT * FROM schema_suggestions ORDER BY created_at DESC"
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM schema_suggestions WHERE created_by_user_id = ? ORDER BY created_at DESC",
                (created_by_user_id,),
            )
        rows = await cursor.fetchall()
        suggestions = []
        for row in rows:
            item = dict(row)
            item["file_ids"] = _loads_if_json(item.get("file_ids")) or []
            item["schema_definition"] = (
                _loads_if_json(item.get("schema_definition")) or {}
            )
            item["field_descriptions"] = (
                _loads_if_json(item.get("field_descriptions")) or {}
            )
            suggestions.append(item)
        return suggestions


async def create_job_correction(
    job_id: int,
    original_result: Dict[str, Any],
    corrected_result: Dict[str, Any],
    diff_summary: List[Dict[str, Any]],
    feedback_tags: List[str],
    reviewer_user_id: Optional[int],
    notes: Optional[str] = None,
) -> int:
    async with connect() as db:
        cursor = await db.execute(
            """
            INSERT INTO job_corrections (
                job_id, original_result, corrected_result, diff_summary,
                feedback_tags, notes, reviewer_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                json.dumps(original_result),
                json.dumps(corrected_result),
                json.dumps(diff_summary),
                json.dumps(feedback_tags),
                notes,
                reviewer_user_id,
            ),
        )
        await db.execute(
            "UPDATE processing_jobs SET correction_status = ? WHERE id = ?",
            ("corrected", job_id),
        )
        await db.commit()
        return cursor.lastrowid


async def list_job_corrections(job_id: int) -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT jc.*, u.username AS reviewer_username
            FROM job_corrections jc
            LEFT JOIN users u ON u.id = jc.reviewer_user_id
            WHERE jc.job_id = ?
            ORDER BY jc.created_at DESC
            """,
            (job_id,),
        )
        rows = await cursor.fetchall()
        corrections = []
        for row in rows:
            item = dict(row)
            for key in (
                "original_result",
                "corrected_result",
                "diff_summary",
                "feedback_tags",
            ):
                item[key] = _loads_if_json(item.get(key))
            corrections.append(item)
        return corrections


async def get_latest_job_correction(job_id: int) -> Optional[Dict[str, Any]]:
    corrections = await list_job_corrections(job_id)
    return corrections[0] if corrections else None


async def upsert_prompt_learning_entry(
    schema_name: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    processing_method: Optional[str],
    entry_type: str,
    content: str,
    source_correction_count: int,
    last_correction_id: int,
) -> int:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id FROM prompt_learning_entries
            WHERE COALESCE(schema_name, '') = COALESCE(?, '')
              AND COALESCE(provider, '') = COALESCE(?, '')
              AND COALESCE(model, '') = COALESCE(?, '')
              AND COALESCE(processing_method, '') = COALESCE(?, '')
              AND entry_type = ?
            """,
            (schema_name, provider, model, processing_method, entry_type),
        )
        row = await cursor.fetchone()
        if row:
            await db.execute(
                """
                UPDATE prompt_learning_entries
                SET content = ?, source_correction_count = ?, last_correction_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (content, source_correction_count, last_correction_id, row["id"]),
            )
            await db.commit()
            return row["id"]

        cursor = await db.execute(
            """
            INSERT INTO prompt_learning_entries (
                schema_name, provider, model, processing_method,
                entry_type, content, source_correction_count, last_correction_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                schema_name,
                provider,
                model,
                processing_method,
                entry_type,
                content,
                source_correction_count,
                last_correction_id,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def list_prompt_learning_entries(
    schema_name: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM prompt_learning_entries WHERE 1=1"
        params: List[Any] = []
        if schema_name:
            query += " AND schema_name = ?"
            params.append(schema_name)
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        if model:
            query += " AND model = ?"
            params.append(model)
        query += " ORDER BY updated_at DESC"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_job_analytics(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    schema_name: Optional[str] = None,
    processing_method: Optional[str] = None,
    document_type: Optional[str] = None,
) -> Dict[str, Any]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        where = ["j.status IN ('success', 'error')"]
        params: List[Any] = []
        if date_from:
            where.append("date(j.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            where.append("date(j.created_at) <= date(?)")
            params.append(date_to)
        if provider:
            where.append("j.provider = ?")
            params.append(provider)
        if model:
            where.append("j.model = ?")
            params.append(model)
        if schema_name:
            where.append("j.schema_name = ?")
            params.append(schema_name)
        if processing_method:
            where.append("j.processing_method = ?")
            params.append(processing_method)
        if document_type:
            where.append("j.document_type = ?")
            params.append(document_type)

        where_sql = " AND ".join(where)

        overview_cursor = await db.execute(
            f"""
            SELECT
                COUNT(*) AS total_jobs,
                SUM(CASE WHEN j.status = 'success' THEN 1 ELSE 0 END) AS successful_jobs,
                SUM(COALESCE(j.estimated_cost, 0)) AS total_cost,
                AVG(CASE WHEN j.processing_time_seconds IS NOT NULL THEN j.processing_time_seconds END) AS avg_latency,
                SUM(CASE WHEN jc.id IS NOT NULL THEN 1 ELSE 0 END) AS corrected_jobs
            FROM processing_jobs j
            LEFT JOIN (
                SELECT DISTINCT job_id, id FROM job_corrections
            ) jc ON jc.job_id = j.id
            WHERE {where_sql}
            """,
            params,
        )
        overview = dict(await overview_cursor.fetchone())

        pipeline_cursor = await db.execute(
            f"""
            SELECT
                j.processing_method,
                COUNT(*) AS job_count,
                SUM(COALESCE(j.estimated_cost, 0)) AS total_cost,
                AVG(COALESCE(j.processing_time_seconds, 0)) AS avg_latency
            FROM processing_jobs j
            WHERE {where_sql}
            GROUP BY j.processing_method
            ORDER BY job_count DESC
            """,
            params,
        )
        pipeline_distribution = [dict(row) for row in await pipeline_cursor.fetchall()]

        provider_cursor = await db.execute(
            f"""
            SELECT
                j.provider,
                j.model,
                j.schema_name,
                COUNT(*) AS total_jobs,
                SUM(CASE WHEN j.status = 'success' THEN 1 ELSE 0 END) AS successful_jobs,
                SUM(COALESCE(j.estimated_cost, 0)) AS total_cost,
                AVG(COALESCE(j.processing_time_seconds, 0)) AS avg_latency,
                SUM(CASE WHEN jc.job_id IS NOT NULL THEN 1 ELSE 0 END) AS corrected_jobs
            FROM processing_jobs j
            LEFT JOIN (SELECT DISTINCT job_id FROM job_corrections) jc ON jc.job_id = j.id
            WHERE {where_sql}
            GROUP BY j.provider, j.model, j.schema_name
            ORDER BY total_jobs DESC, total_cost DESC
            """,
            params,
        )
        provider_rows = [dict(row) for row in await provider_cursor.fetchall()]

        daily_cursor = await db.execute(
            f"""
            SELECT
                date(j.created_at) AS day,
                COUNT(*) AS total_jobs,
                SUM(COALESCE(j.estimated_cost, 0)) AS total_cost,
                SUM(CASE WHEN jc.job_id IS NOT NULL THEN 1 ELSE 0 END) AS corrected_jobs
            FROM processing_jobs j
            LEFT JOIN (SELECT DISTINCT job_id FROM job_corrections) jc ON jc.job_id = j.id
            WHERE {where_sql}
            GROUP BY date(j.created_at)
            ORDER BY day DESC
            LIMIT 30
            """,
            params,
        )
        daily_trend = [dict(row) for row in await daily_cursor.fetchall()]

        correction_patterns_cursor = await db.execute(
            """
            SELECT
                value AS feedback_tag,
                COUNT(*) AS frequency
            FROM job_corrections jc,
                 json_each(COALESCE(jc.feedback_tags, '[]'))
            GROUP BY value
            ORDER BY frequency DESC
            LIMIT 10
            """
        )
        correction_patterns = [
            dict(row) for row in await correction_patterns_cursor.fetchall()
        ]

        benchmark_cursor = await db.execute(
            """
            SELECT
                provider,
                model,
                AVG(overall_accuracy) AS benchmark_accuracy,
                AVG(total_cost / NULLIF(sample_count, 0)) AS cost_per_document,
                AVG(avg_latency) AS benchmark_latency,
                COUNT(*) AS run_count
            FROM benchmark_runs
            WHERE overall_accuracy IS NOT NULL
            GROUP BY provider, model
            ORDER BY benchmark_accuracy DESC
            """
        )
        benchmark_accuracy = [dict(row) for row in await benchmark_cursor.fetchall()]

        for row in provider_rows:
            total_jobs = row["total_jobs"] or 0
            successful_jobs = row["successful_jobs"] or 0
            corrected_jobs = row["corrected_jobs"] or 0
            total_cost = row["total_cost"] or 0
            row["success_rate"] = (
                round(successful_jobs / total_jobs, 4) if total_jobs else 0.0
            )
            row["correction_rate"] = (
                round(corrected_jobs / total_jobs, 4) if total_jobs else 0.0
            )
            row["cost_per_successful_job"] = (
                round(total_cost / successful_jobs, 6) if successful_jobs else 0.0
            )
            row["cost_per_corrected_job"] = (
                round(total_cost / corrected_jobs, 6) if corrected_jobs else 0.0
            )

        total_jobs = overview.get("total_jobs") or 0
        corrected_jobs = overview.get("corrected_jobs") or 0
        successful_jobs = overview.get("successful_jobs") or 0
        total_cost = overview.get("total_cost") or 0

        overview["success_rate"] = (
            round(successful_jobs / total_jobs, 4) if total_jobs else 0.0
        )
        overview["production_correction_rate"] = (
            round(corrected_jobs / total_jobs, 4) if total_jobs else 0.0
        )
        overview["cost_per_successful_job"] = (
            round(total_cost / successful_jobs, 6) if successful_jobs else 0.0
        )
        overview["cost_per_corrected_job"] = (
            round(total_cost / corrected_jobs, 6) if corrected_jobs else 0.0
        )

        return {
            "overview": overview,
            "provider_breakdown": provider_rows,
            "pipeline_distribution": pipeline_distribution,
            "daily_trend": daily_trend,
            "benchmark_accuracy": benchmark_accuracy,
            "correction_patterns": correction_patterns,
        }


async def enqueue_job(
    job_id: int,
    task_type: str,
    file_path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Queue a processing job for durable background execution."""
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
    """Atomically claim one pending queue record for the given worker."""
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
        item["payload"] = _loads_if_json(item.get("payload")) or {}
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
    """
    Requeue queue records left in processing state after an unclean shutdown.

    Returns number of queue rows reset to pending.
    """
    async with connect() as db:
        cursor = await db.execute(
            "SELECT job_id FROM job_queue WHERE status = 'processing'"
        )
        stuck_ids = [row[0] for row in await cursor.fetchall()]
        if not stuck_ids:
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

import aiosqlite
from typing import Optional, List, Dict, Any
from database.pool import connect

_SUCCESS_RATE_SQL = """
    LEFT JOIN (
        SELECT
            run_id,
            CAST(SUM(CASE WHEN accuracy_score >= 0.5 THEN 1 ELSE 0 END) AS REAL)
                / NULLIF(COUNT(*), 0) AS success_rate
        FROM benchmark_results
        GROUP BY run_id
    ) stats ON stats.run_id = br.id
"""


async def create_benchmark_run(
    dataset: str,
    provider: str,
    model: str,
    sample_count: int,
    processing_method: str = "vision",
) -> int:
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
    async with connect() as db:
        await db.execute(
            """UPDATE benchmark_runs
               SET overall_accuracy = ?, avg_latency = ?, total_cost = ?,
                   total_prompt_tokens = ?, total_completion_tokens = ?,
                   completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
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
    offset: int = 0,
    dataset: Optional[str] = None,
    provider: Optional[str] = None,
) -> List[Dict[str, Any]]:
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
        params.append(offset)
        cursor = await db.execute(
            f"""
            SELECT br.*, stats.success_rate AS success_rate
            FROM benchmark_runs br
            {_SUCCESS_RATE_SQL}
            {where_sql}
            ORDER BY br.started_at DESC
            LIMIT ? OFFSET ?
            """,
            params,
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_benchmark_run(run_id: int) -> Optional[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"""
            SELECT br.*, stats.success_rate AS success_rate
            FROM benchmark_runs br
            {_SUCCESS_RATE_SQL}
            WHERE br.id = ?
            """,
            (run_id,),
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_benchmark_results(run_id: int) -> List[Dict[str, Any]]:
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


async def get_model_comparison(
    dataset: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        where_clauses = ["br.overall_accuracy IS NOT NULL"]
        params: List[Any] = []

        if dataset:
            where_clauses.append("br.dataset = ?")
            params.append(dataset)

        where_sql = " AND ".join(where_clauses)
        params.append(limit)

        cursor = await db.execute(
            f"""
            WITH ranked_runs AS (
                SELECT
                    br.id AS run_id,
                    br.provider,
                    br.model,
                    br.processing_method,
                    br.sample_count,
                    br.overall_accuracy,
                    br.avg_latency,
                    br.total_cost,
                    br.total_prompt_tokens,
                    br.total_completion_tokens,
                    br.started_at,
                    stats.success_rate,
                    ROW_NUMBER() OVER (
                        PARTITION BY br.provider, br.model, COALESCE(br.processing_method, '')
                        ORDER BY COALESCE(br.completed_at, br.started_at) DESC, br.id DESC
                    ) AS row_num
                FROM benchmark_runs br
                {_SUCCESS_RATE_SQL}
                WHERE {where_sql}
            )
            SELECT
                run_id,
                provider,
                model,
                processing_method,
                sample_count,
                overall_accuracy,
                avg_latency,
                total_cost,
                total_prompt_tokens,
                total_completion_tokens,
                success_rate,
                started_at
            FROM ranked_runs
            WHERE row_num = 1
            ORDER BY overall_accuracy DESC
            LIMIT ?
            """,
            params,
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_benchmarked_models_summary() -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                br.provider,
                br.model,
                MAX(br.id) AS run_id,
                AVG(br.overall_accuracy) AS accuracy,
                AVG(br.avg_latency) AS avg_latency,
                SUM(br.total_cost) AS total_cost,
                SUM(br.sample_count) AS sample_count,
                AVG(stats.success_rate) AS success_rate
            FROM benchmark_runs br
            LEFT JOIN (
                SELECT
                    run_id,
                    CAST(SUM(CASE WHEN accuracy_score >= 0.5 THEN 1 ELSE 0 END) AS REAL)
                        / NULLIF(COUNT(*), 0) AS success_rate
                FROM benchmark_results
                GROUP BY run_id
            ) stats ON stats.run_id = br.id
            GROUP BY br.provider, br.model
            """
        )
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

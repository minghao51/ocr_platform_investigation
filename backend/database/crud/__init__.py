import json
from typing import Any


def _loads_if_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


from database.crud.users import (
    create_user,
    get_user_by_username,
    get_user_by_id,
    list_users,
    increment_token_version,
)
from database.crud.jobs import (
    create_job,
    update_job_status,
    get_job,
    list_jobs,
    delete_job,
    update_job_metadata,
    update_quality_info,
    create_uploaded_file,
    get_uploaded_file,
)
from database.crud.schemas import (
    create_schema,
    get_schema,
    list_schemas,
    create_schema_suggestion,
    get_schema_suggestion,
    list_schema_suggestions,
    create_job_correction,
    list_job_corrections,
    get_latest_job_correction,
    upsert_prompt_learning_entry,
    list_prompt_learning_entries,
)
from database.crud.benchmarks import (
    create_benchmark_run,
    update_benchmark_run,
    add_benchmark_result,
    list_benchmark_runs,
    get_benchmark_run,
    get_benchmark_results,
    get_job_analytics,
)
from database.crud.queue import (
    enqueue_job,
    claim_next_queued_job,
    mark_queue_job_completed,
    mark_queue_job_failed,
    recover_inflight_queue_jobs,
)

__all__ = [
    "create_user",
    "get_user_by_username",
    "get_user_by_id",
    "list_users",
    "increment_token_version",
    "create_job",
    "update_job_status",
    "get_job",
    "list_jobs",
    "delete_job",
    "update_job_metadata",
    "update_quality_info",
    "create_uploaded_file",
    "get_uploaded_file",
    "create_schema",
    "get_schema",
    "list_schemas",
    "create_schema_suggestion",
    "get_schema_suggestion",
    "list_schema_suggestions",
    "create_job_correction",
    "list_job_corrections",
    "get_latest_job_correction",
    "upsert_prompt_learning_entry",
    "list_prompt_learning_entries",
    "create_benchmark_run",
    "update_benchmark_run",
    "add_benchmark_result",
    "list_benchmark_runs",
    "get_benchmark_run",
    "get_benchmark_results",
    "get_job_analytics",
    "enqueue_job",
    "claim_next_queued_job",
    "mark_queue_job_completed",
    "mark_queue_job_failed",
    "recover_inflight_queue_jobs",
]

import json
from typing import Any, Dict


def _parse_job_result(raw_result: Any) -> Any:
    if isinstance(raw_result, str):
        try:
            return json.loads(raw_result)
        except json.JSONDecodeError:
            return raw_result
    return raw_result


def serialize_job(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "job_id": job["id"],
        "file_name": job["file_name"],
        "file_type": job["file_type"],
        "status": job["status"],
        "provider": job["provider"],
        "model": job["model"],
        "schema_name": job["schema_name"],
        "created_at": job["created_at"],
        "updated_at": job.get("completed_at")
        or job.get("updated_at")
        or job["created_at"],
        "processing_time": job.get("processing_time_seconds"),
        "processing_method": job.get("processing_method"),
        "result": _parse_job_result(job.get("result")),
        "metadata": _parse_job_result(job.get("metadata")),
        "error": job.get("error_message"),
    }

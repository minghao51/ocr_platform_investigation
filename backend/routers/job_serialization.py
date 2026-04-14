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
    metadata = _parse_job_result(job.get("metadata"))
    correction_summary = (
        metadata.get("correction_summary") if isinstance(metadata, dict) else None
    )
    hybrid_diagnostics = metadata.get("hybrid") if isinstance(metadata, dict) else None
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
        "metadata": metadata,
        "error": job.get("error_message"),
        "prompt_tokens": job.get("prompt_tokens"),
        "completion_tokens": job.get("completion_tokens"),
        "estimated_cost": job.get("estimated_cost"),
        "document_type": job.get("document_type"),
        "correction_status": job.get("correction_status") or "uncorrected",
        "correction_summary": correction_summary,
        "hybrid_diagnostics": hybrid_diagnostics,
        # Quality gate info
        "quality_score": job.get("quality_score"),
        "quality_checks": _parse_job_result(job.get("quality_checks")),
        "preprocessing_applied": _parse_job_result(job.get("preprocessing_applied")),
    }

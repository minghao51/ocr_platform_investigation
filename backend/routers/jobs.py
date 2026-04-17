from fastapi import APIRouter, HTTPException, Depends, Request
from database import crud
from dependencies import get_current_user, get_optional_user
from routers.job_serialization import serialize_job
from routers.shared import ensure_job_access
from models.schemas import JobCorrectionRequest
from services.prompt_learning import PromptLearningService
from typing import Any, Optional

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _diff_results(original: Any, corrected: Any, path: str = "") -> list[dict]:
    if type(original) is not type(corrected):
        return [
            {
                "path": path or "$",
                "change_type": "type_changed",
                "before": original,
                "after": corrected,
            }
        ]

    if isinstance(original, dict):
        changes = []
        keys = sorted(set(original.keys()) | set(corrected.keys()))
        for key in keys:
            next_path = f"{path}.{key}" if path else key
            if key not in original:
                changes.append(
                    {
                        "path": next_path,
                        "change_type": "added",
                        "before": None,
                        "after": corrected[key],
                    }
                )
            elif key not in corrected:
                changes.append(
                    {
                        "path": next_path,
                        "change_type": "removed",
                        "before": original[key],
                        "after": None,
                    }
                )
            else:
                changes.extend(_diff_results(original[key], corrected[key], next_path))
        return changes

    if isinstance(original, list):
        changes = []
        max_length = max(len(original), len(corrected))
        for index in range(max_length):
            next_path = f"{path}[{index}]"
            if index >= len(original):
                changes.append(
                    {
                        "path": next_path,
                        "change_type": "added",
                        "before": None,
                        "after": corrected[index],
                    }
                )
            elif index >= len(corrected):
                changes.append(
                    {
                        "path": next_path,
                        "change_type": "removed",
                        "before": original[index],
                        "after": None,
                    }
                )
            else:
                changes.extend(
                    _diff_results(original[index], corrected[index], next_path)
                )
        return changes

    if original != corrected:
        return [
            {
                "path": path or "$",
                "change_type": "updated",
                "before": original,
                "after": corrected,
            }
        ]
    return []


@router.get("/")
async def list_jobs(
    status: Optional[str] = None,
    provider: str = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """List all processing jobs with optional filters"""
    limit = max(1, min(limit, 100))
    user_id = (
        None if current_user.get("is_admin", False) else current_user.get("user_id")
    )
    jobs = await crud.list_jobs(
        status=status, provider=provider, user_id=user_id, limit=limit
    )
    return [serialize_job(j) for j in jobs]


@router.get("/{job_id}")
async def get_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """Get job by ID"""
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ensure_job_access(job, current_user)

    return serialize_job(job)


@router.delete("/{job_id}")
async def delete_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """Delete job by ID"""
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ensure_job_access(job, current_user)
    success = await crud.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully"}


@router.get("/{job_id}/corrections")
async def get_job_corrections(
    job_id: int,
    request: Request,
    current_user: dict | None = Depends(get_optional_user),
):
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ensure_job_access(job, current_user, request.headers.get("X-Guest-Token"))
    return await crud.list_job_corrections(job_id)


@router.post("/{job_id}/corrections")
async def create_job_correction(
    job_id: int,
    payload: JobCorrectionRequest,
    current_user: dict = Depends(get_current_user),
):
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ensure_job_access(job, current_user)
    if job.get("status") != "success":
        raise HTTPException(
            status_code=400, detail="Only successful jobs can be corrected"
        )

    original_result = serialize_job(job).get("result")
    if not isinstance(original_result, dict):
        raise HTTPException(
            status_code=400, detail="Job has no structured result to correct"
        )

    diff_summary = _diff_results(original_result, payload.corrected_result)
    correction_id = await crud.create_job_correction(
        job_id=job_id,
        original_result=original_result,
        corrected_result=payload.corrected_result,
        diff_summary=diff_summary,
        feedback_tags=payload.feedback_tags,
        reviewer_user_id=current_user.get("user_id"),
        notes=payload.notes,
    )

    await crud.update_job_metadata(
        job_id,
        {
            "correction_summary": {
                "latest_correction_id": correction_id,
                "feedback_tags": payload.feedback_tags,
                "change_count": len(diff_summary),
            }
        },
    )

    learning_service = PromptLearningService()
    await learning_service.update_from_correction(
        job=job,
        correction_id=correction_id,
        diff_summary=diff_summary,
        feedback_tags=payload.feedback_tags,
    )

    latest = await crud.get_latest_job_correction(job_id)
    return latest

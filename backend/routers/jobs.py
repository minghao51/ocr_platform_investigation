from fastapi import APIRouter, HTTPException, Depends
from database import crud
import json
from dependencies import get_current_user

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/")
async def list_jobs(
    status: str = None,
    provider: str = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """List all processing jobs with optional filters"""
    try:
        limit = max(1, min(limit, 100))
        user_id = (
            None if current_user.get("is_admin", False) else current_user.get("user_id")
        )
        jobs = await crud.list_jobs(
            status=status, provider=provider, user_id=user_id, limit=limit
        )
        return [
            {
                "job_id": j["id"],
                "file_name": j["file_name"],
                "file_type": j["file_type"],
                "status": j["status"],
                "provider": j["provider"],
                "model": j["model"],
                "schema_name": j["schema_name"],
                "created_at": j["created_at"],
                "updated_at": j.get("completed_at")
                or j.get("updated_at")
                or j["created_at"],
                "processing_time": j.get("processing_time_seconds"),
                "processing_method": j.get("processing_method"),
                "result": json.loads(j["result"]) if j.get("result") else None,
                "error": j.get("error_message"),
            }
            for j in jobs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}")
async def get_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """Get job by ID"""
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not current_user.get("is_admin", False) and job.get(
        "user_id"
    ) != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")

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
        "result": json.loads(job["result"]) if job.get("result") else None,
        "error": job.get("error_message"),
    }


@router.delete("/{job_id}")
async def delete_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """Delete job by ID"""
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not current_user.get("is_admin", False) and job.get(
        "user_id"
    ) != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    success = await crud.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully"}

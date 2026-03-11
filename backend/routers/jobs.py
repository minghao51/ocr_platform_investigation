from fastapi import APIRouter, HTTPException, Depends
from database import crud
from dependencies import get_current_user
from routers.job_serialization import serialize_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/")
async def list_jobs(
    status: str = None,
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
    if not current_user.get("is_admin", False) and job.get(
        "user_id"
    ) != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")

    return serialize_job(job)


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

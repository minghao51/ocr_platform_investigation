import hmac

from fastapi import HTTPException, Request, Depends
from typing import Optional

from database import crud
from dependencies import get_current_user, get_optional_user


def is_admin(user: dict) -> bool:
    return bool(user.get("is_admin", False))


def ensure_file_access(
    file_record: dict, current_user: dict | None = None, guest_token: str | None = None
) -> None:
    current_user = current_user or {}
    if is_admin(current_user):
        return
    if current_user.get("user_id") is not None:
        if file_record.get("user_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        return
    if (
        guest_token
        and file_record.get("guest_token")
        and hmac.compare_digest(file_record["guest_token"], guest_token)
    ):
        return
    raise HTTPException(status_code=403, detail="Access denied")


def ensure_job_access(
    job: dict, current_user: dict | None = None, guest_token: str | None = None
) -> None:
    current_user = current_user or {}
    if is_admin(current_user):
        return
    if current_user.get("user_id") is not None:
        if job.get("user_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        return
    if (
        guest_token
        and job.get("guest_token")
        and hmac.compare_digest(job["guest_token"], guest_token)
    ):
        return
    raise HTTPException(status_code=403, detail="Access denied")


def _get_guest_token(request: Request) -> Optional[str]:
    return request.headers.get("X-Guest-Token")


async def get_accessible_file(
    file_id: str,
    request: Request,
    current_user: dict | None = Depends(get_optional_user),
) -> dict:
    file_record = await crud.get_uploaded_file(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    ensure_file_access(file_record, current_user, _get_guest_token(request))
    return file_record


async def get_accessible_file_authenticated(
    file_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict:
    file_record = await crud.get_uploaded_file(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    ensure_file_access(file_record, current_user, _get_guest_token(request))
    return file_record


async def get_accessible_job(
    job_id: int,
    request: Request,
    current_user: dict | None = Depends(get_optional_user),
) -> dict:
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ensure_job_access(job, current_user, _get_guest_token(request))
    return job


async def get_accessible_job_authenticated(
    job_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict:
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ensure_job_access(job, current_user, _get_guest_token(request))
    return job

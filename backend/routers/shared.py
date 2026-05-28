import hmac

from fastapi import HTTPException


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

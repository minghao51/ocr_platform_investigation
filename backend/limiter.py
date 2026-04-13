"""
Rate limiter configuration for the API.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from auth import verify_token
from config import get_settings
import time


def _get_request_user(request: Request) -> dict | None:
    """Best-effort JWT decode for rate-limit keying and admin exemptions."""
    cached = getattr(request.state, "rate_limit_user", None)
    if cached is not None:
        return cached

    authorization = request.headers.get("Authorization", "")
    payload = None
    if authorization.startswith("Bearer "):
        payload = verify_token(authorization.split(" ", 1)[1])

    request.state.rate_limit_user = payload
    return payload


def get_rate_limit_key(request: Request) -> str:
    """Prefer authenticated user IDs so shared demo IPs do not collide."""
    user = _get_request_user(request)
    if user and user.get("is_admin", False) and user.get("user_id") is not None:
        return f"admin:{user['user_id']}:{time.time_ns()}"
    if user and user.get("user_id") is not None:
        return f"user:{user['user_id']}"
    return get_remote_address(request)


def should_exempt_rate_limit(request: Request) -> bool:
    """Admin/master accounts bypass per-minute request caps."""
    user = _get_request_user(request)
    return bool(user and user.get("is_admin", False))


def get_rate_limit_value(*_args, **_kwargs) -> str:
    """Return the configured per-minute limit for OCR actions."""
    return f"{get_settings().rate_limit_per_minute}/minute"


limiter = Limiter(key_func=get_rate_limit_key)


def get_user_id(request: Request) -> str:
    """Get user ID from request for rate limiting."""
    user = _get_request_user(request)
    if user and user.get("user_id") is not None:
        return str(user["user_id"])
    return get_remote_address(request)

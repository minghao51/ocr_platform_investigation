"""
FastAPI dependencies for authentication.
"""

from functools import lru_cache
from pathlib import Path
from fastapi import Header, HTTPException, Depends, status
from typing import Optional, Tuple
from auth import verify_token
from config import get_settings
import aiosqlite
from datetime import date
from database.pool import get_db_path


@lru_cache
def _get_cached_db_path() -> Path:
    """Cache DB path to avoid repeated settings lookups."""
    return get_db_path()


async def _get_user_usage(user_id: int) -> Tuple[int, str, bool]:
    """Fetch user's daily usage stats from database."""
    async with aiosqlite.connect(_get_cached_db_path()) as db:
        cursor = await db.execute(
            "SELECT daily_requests, last_request_date, is_limited FROM users WHERE id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row:
            return row
        return (0, "", False)


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify JWT token and return current user.

    Raises HTTPException if token is missing or invalid.
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def check_daily_limit(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Check if user has exceeded their daily request limit.

    Limited demo users have a daily cap. Admin users bypass the cap.
    """
    if current_user.get("is_admin", False):
        return current_user

    daily_request_limit = get_settings().demo_daily_request_limit
    user_id = current_user.get("user_id")
    today = date.today().isoformat()

    if user_id is None:
        return current_user
    daily_requests, last_request_date, is_limited = await _get_user_usage(user_id)

    if last_request_date != today:
        daily_requests = 0

    if not is_limited:
        return current_user

    if daily_requests >= daily_request_limit:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Daily demo limit ({daily_request_limit} requests) exceeded. "
                "Try again tomorrow or ask an admin/master account for help."
            ),
        )

    return current_user


async def increment_daily_limit(user_id: int):
    """Increment the daily request count for a limited demo user."""
    today = date.today().isoformat()

    daily_requests, last_request_date, is_limited = await _get_user_usage(user_id)

    if not is_limited:
        return

    if last_request_date != today:
        daily_requests = 0

    async with aiosqlite.connect(_get_cached_db_path()) as db:
        await db.execute(
            "UPDATE users SET daily_requests = ?, last_request_date = ? WHERE id = ?",
            (daily_requests + 1, today, user_id),
        )
        await db.commit()

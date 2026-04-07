"""
FastAPI dependencies for authentication.
"""

from functools import lru_cache
from pathlib import Path
from fastapi import Header, HTTPException, Depends, status
from typing import Optional
from auth import verify_token
import aiosqlite
from datetime import date
from database.pool import get_db_path

# Daily request limit for test users
DAILY_REQUEST_LIMIT = 5


@lru_cache
def _get_cached_db_path() -> Path:
    """Cache DB path to avoid repeated settings lookups."""
    return get_db_path()


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

    For test users, limits apply. Admin users are unlimited.
    """
    # Admins bypass the limit
    if current_user.get("is_admin", False):
        return current_user

    user_id = current_user.get("user_id")
    today = date.today().isoformat()

    async with aiosqlite.connect(_get_cached_db_path()) as db:
        # Get user's usage stats
        cursor = await db.execute(
            "SELECT daily_requests, last_request_date, is_limited FROM users WHERE id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            return current_user

        daily_requests, last_request_date, is_limited = row

        # Reset daily count if it's a new day
        if last_request_date != today:
            daily_requests = 0

        # Check if user is blocked
        if is_limited:
            raise HTTPException(
                status_code=403,
                detail="Account limited. Contact administrator for more credits.",
            )

        # Check daily limit
        if daily_requests >= DAILY_REQUEST_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit ({DAILY_REQUEST_LIMIT} requests) exceeded. Try again tomorrow.",
            )

    return current_user


async def increment_daily_limit(user_id: int):
    """Increment the daily request count for a user."""
    today = date.today().isoformat()

    async with aiosqlite.connect(_get_cached_db_path()) as db:
        # Get current stats
        cursor = await db.execute(
            "SELECT daily_requests, last_request_date FROM users WHERE id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            return

        daily_requests, last_request_date = row

        # Reset if new day
        if last_request_date != today:
            daily_requests = 0

        # Increment
        await db.execute(
            "UPDATE users SET daily_requests = ?, last_request_date = ? WHERE id = ?",
            (daily_requests + 1, today, user_id),
        )
        await db.commit()

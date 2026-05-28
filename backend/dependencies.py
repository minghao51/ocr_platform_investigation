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
from database.crud.users import get_user_by_id


@lru_cache
def _get_cached_db_path() -> Path:
    return get_db_path()


async def _validate_token_version(token_data: dict) -> None:
    token_version = token_data.get("token_version")
    user_id = token_data.get("user_id")
    if token_version is not None and user_id is not None:
        user_record = await get_user_by_id(user_id)
        if not user_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        current_token_version = int(user_record.get("token_version") or 0)
        if current_token_version != int(token_version):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )


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

    await _validate_token_version(payload)

    return payload


async def get_optional_user(
    authorization: Optional[str] = Header(None),
) -> Optional[dict]:
    """Best-effort JWT verification for routes that also allow guest access."""
    if authorization is None:
        return None

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1]
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await _validate_token_version(payload)

    return payload


async def check_and_increment_daily_limit(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Atomically check and increment daily request limit.

    Limited demo users have a daily cap. Admin users bypass the cap.
    Uses atomic SQL UPDATE to prevent race conditions.

    Raises HTTPException 429 if daily limit exceeded.
    """
    if current_user.get("is_admin", False):
        return current_user

    daily_request_limit = get_settings().demo_daily_request_limit
    user_id = current_user.get("user_id")

    if user_id is None:
        return current_user

    async with aiosqlite.connect(_get_cached_db_path()) as db:
        # Single atomic operation: check, increment, return new count
        # Uses CASE to reset count when date changes, otherwise increment
        cursor = await db.execute(
            """
            UPDATE users
            SET daily_requests = CASE
                WHEN last_request_date != ? THEN 1
                ELSE daily_requests + 1
            END,
            last_request_date = ?
            WHERE id = ? AND is_limited = 1
            RETURNING daily_requests, last_request_date, is_limited
        """,
            (date.today().isoformat(), date.today().isoformat(), user_id),
        )

        row = await cursor.fetchone()
        await db.commit()

        # User not found or not limited - no restrictions apply
        if row is None:
            return current_user

        daily_requests, last_request_date, is_limited = row

        if is_limited and daily_requests > daily_request_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Daily demo limit ({daily_request_limit} requests) exceeded. Try again tomorrow.",
            )

    return current_user


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Allow only admin users to access privileged endpoints."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

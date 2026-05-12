"""
Authentication utilities for JWT tokens and password hashing.
"""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from config import get_settings

settings = get_settings()

# Password hashing context - using argon2 (more secure, no bcrypt compatibility issues)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: int,
    username: str,
    is_admin: bool = False,
    token_version: int | None = None,
) -> str:
    """Create a JWT access token."""
    expires_delta = timedelta(hours=settings.jwt_expiration_hours)
    now_utc = datetime.now(timezone.utc)
    expire = now_utc + expires_delta

    to_encode = {
        "user_id": user_id,
        "username": username,
        "is_admin": is_admin,
        "exp": expire,
        "iat": now_utc,
    }
    if token_version is not None:
        to_encode["token_version"] = token_version

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token and return the payload.

    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "is_admin": payload.get("is_admin", False),
            "token_version": payload.get("token_version"),
        }
    except jwt.PyJWTError:
        return None

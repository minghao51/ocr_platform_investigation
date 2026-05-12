"""
Authentication router - handles login and token management.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel
from database import crud
from auth import verify_password, create_access_token
from dependencies import get_current_user
from limiter import limiter, get_login_rate_limit_key, get_login_rate_limit_value

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=LoginResponse)
@limiter.limit(get_login_rate_limit_value, key_func=get_login_rate_limit_key)
async def login(request: Request, payload: LoginRequest):
    """
    Authenticate user and return JWT token.

    Raises 401 if credentials are invalid.
    """
    _ = request
    # Get user from database
    user = await crud.get_user_by_username(payload.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Create access token
    access_token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        is_admin=bool(user["is_admin"]),
        token_version=int(user.get("token_version") or 0),
    )

    return LoginResponse(
        access_token=access_token,
        user={
            "id": user["id"],
            "username": user["username"],
            "is_admin": bool(user["is_admin"]),
        },
    )


@router.post("/verify")
async def verify_token_endpoint(current_user: dict = Depends(get_current_user)):
    """
    Verify a JWT token and return user information.

    This endpoint is useful for frontend to check if a token is still valid
    and get current user information.
    """
    return current_user


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Revoke currently active JWTs for this user by rotating token version.
    """
    user_id = current_user.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user context"
        )

    updated = await crud.increment_token_version(int(user_id))
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Logged out successfully"}

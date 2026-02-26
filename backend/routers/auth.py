"""
Authentication router - handles login and token management.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from database import crud
from auth import verify_password, create_access_token
from dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.

    Raises 401 if credentials are invalid.
    """
    # Get user from database
    user = await crud.get_user_by_username(request.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Create access token
    access_token = create_access_token(
        user_id=user["id"], username=user["username"], is_admin=bool(user["is_admin"])
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


# Note: We use JWT tokens which are stateless, so there's no logout endpoint.
# The frontend simply needs to delete the stored token.
# To implement token revocation, we would need to use a token blacklist in Redis/DB.

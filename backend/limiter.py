"""
Rate limiter configuration for the API.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

# Default limiter (IP-based for unauthenticated)
limiter = Limiter(key_func=get_remote_address)


def get_user_id(request: Request) -> str:
    """Get user ID from request for rate limiting."""
    # For unauthenticated requests, fall back to IP
    if hasattr(request.state, "user"):
        return str(request.state.user.get("user_id", get_remote_address(request)))
    return get_remote_address(request)

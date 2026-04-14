"""
Shared test fixtures and utilities for pytest.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from auth import create_access_token


@pytest.fixture
def client():
    """Provide a test client instance."""
    return TestClient(app)


@pytest.fixture
def auth_header():
    """Provide authorization header with admin test token."""
    token = create_access_token(user_id=1, username="test_user", is_admin=True)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user_auth_header():
    """Provide authorization header with non-admin test token."""
    token = create_access_token(
        user_id=2, username="test_user_non_admin", is_admin=False
    )
    return {"Authorization": f"Bearer {token}"}


def get_auth_header(
    user_id: int = 1, username: str = "test_user", is_admin: bool = True
):
    """Get authorization header with custom test token.

    This is a convenience function for inline usage in tests.
    For new tests, prefer using the auth_header fixture.
    """
    token = create_access_token(user_id=user_id, username=username, is_admin=is_admin)
    return {"Authorization": f"Bearer {token}"}

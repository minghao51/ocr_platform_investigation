import pytest
from fastapi.testclient import TestClient
from main import app
from auth import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_header():
    token = create_access_token(user_id=1, username="test_user", is_admin=True)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user_auth_header():
    token = create_access_token(
        user_id=2, username="test_user_non_admin", is_admin=False
    )
    return {"Authorization": f"Bearer {token}"}


def get_auth_header(
    user_id: int = 1, username: str = "test_user", is_admin: bool = True
):
    token = create_access_token(user_id=user_id, username=username, is_admin=is_admin)
    return {"Authorization": f"Bearer {token}"}


def pytest_collection_modifyitems(items):
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        elif "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)

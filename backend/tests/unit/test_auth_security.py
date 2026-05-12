import pytest
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient

from config import get_settings
from database.migrations import run_migrations
from main import app
from auth import hash_password
from database import crud


@pytest.fixture
def auth_test_db(tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "auth-security.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    asyncio.run(run_migrations())
    yield db_path
    get_settings.cache_clear()


def test_get_settings_rejects_default_jwt_secret_in_non_local_env(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    get_settings.cache_clear()

    with pytest.raises(RuntimeError):
        get_settings()

    get_settings.cache_clear()


def test_login_rate_limit_blocks_repeated_attempts(client, auth_test_db):
    _ = auth_test_db
    username = "bruteforce-user"
    headers = {"X-Login-Username": username}
    payload = {"username": username, "password": "wrong-password"}

    for _ in range(5):
        response = client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == 401

    blocked = client.post("/api/auth/login", json=payload, headers=headers)
    assert blocked.status_code == 429


@pytest.fixture
def auth_lifecycle_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "auth-lifecycle.db"
    monkeypatch.setattr("paths.get_db_path", lambda: db_path)
    monkeypatch.setattr("database.pool.get_db_path", lambda: db_path)
    monkeypatch.setattr("database.migrations.get_db_path", lambda: db_path)
    monkeypatch.setattr("dependencies._get_cached_db_path", lambda: db_path)
    monkeypatch.setattr("limiter.limiter.enabled", False)
    get_settings.cache_clear()
    asyncio.run(run_migrations())
    asyncio.run(
        crud.create_user(
            username="lifecycle-user",
            hashed_password=hash_password("secure-pass"),
            is_admin=False,
            is_limited=False,
        )
    )
    yield TestClient(app)
    get_settings.cache_clear()


def test_logout_revokes_token(auth_lifecycle_client):
    client = auth_lifecycle_client

    login = client.post(
        "/api/auth/login",
        json={"username": "lifecycle-user", "password": "secure-pass"},
        headers={"X-Login-Username": "lifecycle-user"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    verify_before = client.post("/api/auth/verify", headers=headers)
    assert verify_before.status_code == 200

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200

    verify_after = client.post("/api/auth/verify", headers=headers)
    assert verify_after.status_code == 401

import pytest
import asyncio

from config import get_settings
from database.migrations import run_migrations


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

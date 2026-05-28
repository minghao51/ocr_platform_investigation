import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from main import app
from database.migrations import run_migrations
from database import crud


@pytest.fixture(autouse=True)
def _disable_rate_limiting(monkeypatch):
    monkeypatch.setattr("limiter.limiter.enabled", False)


@pytest.fixture
def temp_db_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("paths.get_db_path", lambda: db_path)
    monkeypatch.setattr("database.pool.get_db_path", lambda: db_path)
    monkeypatch.setattr("database.migrations.get_db_path", lambda: db_path)
    monkeypatch.setattr("dependencies._get_cached_db_path", lambda: db_path)
    monkeypatch.setattr("routers.upload.UPLOAD_DIR", uploads_dir)

    asyncio.run(run_migrations())
    asyncio.run(crud.create_user("test_user", "hashed_pw_not_real", is_admin=True))
    return tmp_path


@pytest.fixture
def client(temp_db_env):
    return TestClient(app)

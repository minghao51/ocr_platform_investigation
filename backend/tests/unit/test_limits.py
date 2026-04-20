import sqlite3
from datetime import date
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from auth import create_access_token
from dependencies import check_and_increment_daily_limit
from limiter import get_rate_limit_key, should_exempt_rate_limit


def _init_test_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as db:
        db.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                daily_requests INTEGER DEFAULT 0,
                last_request_date TEXT,
                is_limited BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.commit()


def _insert_user(
    db_path: Path,
    *,
    user_id: int,
    username: str,
    is_admin: bool = False,
    is_limited: bool = False,
    daily_requests: int = 0,
    last_request_date: str | None = None,
) -> None:
    with sqlite3.connect(db_path) as db:
        db.execute(
            """
            INSERT INTO users (
                id, username, hashed_password, is_admin,
                daily_requests, last_request_date, is_limited
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                "hashed",
                is_admin,
                daily_requests,
                last_request_date,
                is_limited,
            ),
        )
        db.commit()


def _build_request(token: str | None = None, client_host: str = "127.0.0.1") -> Request:
    headers = []
    if token:
        headers.append((b"authorization", f"Bearer {token}".encode()))

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/process/",
            "headers": headers,
            "client": (client_host, 12345),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


@pytest.fixture
def temp_user_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "limits.db"
    _init_test_db(db_path)
    monkeypatch.setattr("dependencies._get_cached_db_path", lambda: db_path)
    return db_path


@pytest.mark.asyncio
async def test_limited_demo_user_is_allowed_below_daily_cap(temp_user_db: Path):
    _insert_user(
        temp_user_db,
        user_id=7,
        username="guest",
        is_limited=True,
        daily_requests=1,
        last_request_date=date.today().isoformat(),
    )

    current_user = {"user_id": 7, "username": "guest", "is_admin": False}
    assert await check_and_increment_daily_limit(current_user) == current_user

    # Verify count was incremented
    with sqlite3.connect(temp_user_db) as db:
        requests = db.execute(
            "SELECT daily_requests FROM users WHERE id = 7"
        ).fetchone()[0]
    assert requests == 2


@pytest.mark.asyncio
async def test_limited_demo_user_hits_daily_cap(temp_user_db: Path):
    _insert_user(
        temp_user_db,
        user_id=8,
        username="guest-capped",
        is_limited=True,
        daily_requests=5,
        last_request_date=date.today().isoformat(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await check_and_increment_daily_limit(
            {"user_id": 8, "username": "guest-capped", "is_admin": False}
        )

    assert exc_info.value.status_code == 429
    assert "Daily demo limit" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_unlimited_non_admin_user_bypasses_daily_demo_cap(temp_user_db: Path):
    _insert_user(
        temp_user_db,
        user_id=9,
        username="member",
        is_limited=False,
        daily_requests=999,
        last_request_date=date.today().isoformat(),
    )

    current_user = {"user_id": 9, "username": "member", "is_admin": False}
    assert await check_and_increment_daily_limit(current_user) == current_user

    # Non-limited users should not have their count updated
    with sqlite3.connect(temp_user_db) as db:
        requests = db.execute(
            "SELECT daily_requests FROM users WHERE id = 9"
        ).fetchone()[0]
    assert requests == 999


@pytest.mark.asyncio
async def test_check_and_increment_is_atomic(temp_user_db: Path):
    """Verify that check and increment happen atomically."""
    today = date.today().isoformat()
    _insert_user(
        temp_user_db,
        user_id=10,
        username="limited-user",
        is_limited=True,
        daily_requests=4,
        last_request_date=today,
    )

    # First call should succeed (4 -> 5)
    current_user = {"user_id": 10, "username": "limited-user", "is_admin": False}
    assert await check_and_increment_daily_limit(current_user) == current_user

    with sqlite3.connect(temp_user_db) as db:
        requests = db.execute(
            "SELECT daily_requests FROM users WHERE id = 10"
        ).fetchone()[0]
    assert requests == 5

    # Second call should fail (5 -> 6 exceeds limit)
    with pytest.raises(HTTPException) as exc_info:
        await check_and_increment_daily_limit(
            {"user_id": 10, "username": "limited-user", "is_admin": False}
        )
    assert exc_info.value.status_code == 429


def test_rate_limit_uses_user_identity_and_exempts_admin():
    admin_token = create_access_token(user_id=99, username="master", is_admin=True)
    request = _build_request(admin_token, client_host="10.0.0.5")

    assert get_rate_limit_key(request) == "admin:99"
    assert should_exempt_rate_limit(request) is True


def test_rate_limit_falls_back_to_ip_for_guests():
    request = _build_request(client_host="203.0.113.10")

    assert get_rate_limit_key(request) == "203.0.113.10"
    assert should_exempt_rate_limit(request) is False

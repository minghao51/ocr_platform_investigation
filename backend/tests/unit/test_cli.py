import asyncio
from unittest.mock import AsyncMock

import cli


def test_print_help_uses_current_cli_invocation(capsys):
    cli.print_help()

    output = capsys.readouterr().out
    assert "uv run -m backend.cli create-admin" in output
    assert "uv run -m backend.cli export-benchmark" in output


def test_create_admin_user_success(capsys, monkeypatch):
    monkeypatch.setattr(cli.crud, "get_user_by_username", AsyncMock(return_value=None))
    monkeypatch.setattr(cli.crud, "create_user", AsyncMock(return_value=42))

    assert asyncio.run(cli.create_admin_user("admin-user", "secret")) is True

    output = capsys.readouterr().out
    assert "Admin user created successfully" in output
    assert "User ID: 42" in output


def test_create_demo_user_and_list_users(capsys, monkeypatch):
    monkeypatch.setattr(cli, "_demo_limit_label", lambda: "5 requests/day")
    monkeypatch.setattr(cli.crud, "get_user_by_username", AsyncMock(return_value=None))
    monkeypatch.setattr(cli.crud, "create_user", AsyncMock(return_value=7))
    monkeypatch.setattr(
        cli.crud,
        "list_users",
        AsyncMock(
            return_value=[
                {
                    "id": 7,
                    "username": "demo-user",
                    "is_admin": False,
                    "is_limited": True,
                    "daily_requests": 3,
                    "created_at": "2026-06-13T00:00:00",
                }
            ]
        ),
    )

    assert asyncio.run(cli.create_demo_user("demo-user", "secret")) is True
    assert asyncio.run(cli.list_all_users()) is True

    output = capsys.readouterr().out
    assert "Demo user created successfully" in output
    assert "5 requests/day" in output
    assert "demo-user" in output

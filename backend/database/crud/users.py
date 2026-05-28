import aiosqlite
from typing import Optional, Dict, Any, List
from database.pool import connect


async def create_user(
    username: str,
    hashed_password: str,
    is_admin: bool = False,
    is_limited: bool = False,
) -> int:
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO users (username, hashed_password, is_admin, is_limited)
               VALUES (?, ?, ?, ?)""",
            (username, hashed_password, is_admin, is_limited),
        )
        await db.commit()
        return cursor.lastrowid


async def increment_token_version(user_id: int) -> bool:
    async with connect() as db:
        cursor = await db.execute(
            """
            UPDATE users
            SET token_version = COALESCE(token_version, 0) + 1
            WHERE id = ?
            """,
            (user_id,),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def list_users(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, username, is_admin, is_limited, daily_requests, last_request_date, created_at
               FROM users
               ORDER BY created_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

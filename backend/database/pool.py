"""
Simple database connection wrapper for SQLite.

This provides a drop-in replacement for aiosqlite.connect() with
connection pooling for future migration to PostgreSQL/MySQL.
"""

import aiosqlite
import logging
from pathlib import Path
from paths import get_db_path

logger = logging.getLogger(__name__)


class ConnectionWrapper:
    """Wrapper for aiosqlite connection that works with async context manager."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def __aenter__(self) -> aiosqlite.Connection:
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        return self._connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._connection:
            await self._connection.close()
            self._connection = None


def connect(db_path: Path | None = None) -> ConnectionWrapper:
    """
    Get a connection wrapper that works with async context manager.

    Usage:
        async with connect() as db:
            cursor = await db.execute(...)
    """
    return ConnectionWrapper(db_path or get_db_path())


async def close_pool():
    """No-op for compatibility - included for future pool implementation."""
    logger.info("Close pool called (no-op for direct connection mode)")

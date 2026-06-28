"""SQLite connection helper for consistent repo-wide pragmas."""

import aiosqlite
import logging
from pathlib import Path
from paths import get_db_path

logger = logging.getLogger(__name__)


class ConnectionWrapper:
    """Thin async context manager around a single aiosqlite connection."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def __aenter__(self) -> aiosqlite.Connection:
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        # Enable WAL mode for better concurrency and performance
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA busy_timeout=5000")
        await self._connection.execute("PRAGMA foreign_keys=ON")
        return self._connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._connection:
            await self._connection.close()
            self._connection = None


def connect(db_path: Path | None = None) -> ConnectionWrapper:
    """
    Open a single SQLite connection with the repo's standard pragmas applied.

    Usage:
        async with connect() as db:
            cursor = await db.execute(...)
    """
    return ConnectionWrapper(db_path or get_db_path())


async def close_pool():
    """Compatibility no-op for callers that expect shutdown cleanup."""
    logger.info("SQLite helper shutdown called (no persistent pool to close)")

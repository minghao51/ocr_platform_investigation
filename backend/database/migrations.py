import aiosqlite
import asyncio
from pathlib import Path

DB_PATH = Path("./data/ocr_platform.db")

async def init_database():
    """Initialize database with schema"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        # Read and execute schema
        with open("database/schema.sql", "r") as f:
            schema = f.read()

        await db.executescript(schema)
        await db.commit()

        print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    asyncio.run(init_database())

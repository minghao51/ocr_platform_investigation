import aiosqlite
import asyncio
from pathlib import Path

DB_PATH = Path("./data/ocr_platform.db")

async def migrate_processing_method():
    """Add processing_method column to existing processing_jobs table"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if column exists
        cursor = await db.execute("PRAGMA table_info(processing_jobs)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "processing_method" not in column_names:
            print("Adding processing_method column to processing_jobs table...")
            await db.execute(
                "ALTER TABLE processing_jobs ADD COLUMN processing_method TEXT DEFAULT 'vision'"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_processing_method ON processing_jobs(processing_method)"
            )
            await db.commit()
            print("✓ Added processing_method column")
        else:
            print("✓ processing_method column already exists")

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

async def run_migrations():
    """Run all database migrations"""
    await migrate_processing_method()
    print("All migrations completed successfully")

if __name__ == "__main__":
    asyncio.run(run_migrations())

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


async def migrate_users_table():
    """Create users table for authentication"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if users table exists
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        result = await cursor.fetchone()

        if result is None:
            print("Creating users table...")
            await db.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    hashed_password TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
            print("✓ Created users table")
        else:
            print("✓ users table already exists")


async def migrate_user_id_to_jobs():
    """Add user_id column to processing_jobs table"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if column exists
        cursor = await db.execute("PRAGMA table_info(processing_jobs)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "user_id" not in column_names:
            print("Adding user_id column to processing_jobs table...")
            await db.execute(
                "ALTER TABLE processing_jobs ADD COLUMN user_id INTEGER"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON processing_jobs(user_id)"
            )
            await db.commit()
            print("✓ Added user_id column")
        else:
            print("✓ user_id column already exists")

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

async def migrate_user_usage_tracking():
    """Add usage tracking columns to users table"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if column exists
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "daily_requests" not in column_names:
            print("Adding daily_requests column to users table...")
            await db.execute(
                "ALTER TABLE users ADD COLUMN daily_requests INTEGER DEFAULT 0"
            )
            await db.execute(
                "ALTER TABLE users ADD COLUMN last_request_date TEXT"
            )
            await db.execute(
                "ALTER TABLE users ADD COLUMN is_limited BOOLEAN DEFAULT 0"
            )
            await db.commit()
            print("✓ Added usage tracking columns")
        else:
            print("✓ Usage tracking columns already exist")


async def run_migrations():
    """Run all database migrations"""
    await migrate_processing_method()
    await migrate_users_table()
    await migrate_user_id_to_jobs()
    await migrate_user_usage_tracking()
    print("All migrations completed successfully")

if __name__ == "__main__":
    asyncio.run(run_migrations())

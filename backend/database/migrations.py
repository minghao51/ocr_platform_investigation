import aiosqlite
import asyncio
from pathlib import Path
from paths import LEGACY_DB_PATH, get_db_path


def _get_db_path() -> Path:
    return get_db_path()


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


async def migrate_processing_method():
    """Add processing_method column to existing processing_jobs table"""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
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
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
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
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Check if column exists
        cursor = await db.execute("PRAGMA table_info(processing_jobs)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "user_id" not in column_names:
            print("Adding user_id column to processing_jobs table...")
            await db.execute("ALTER TABLE processing_jobs ADD COLUMN user_id INTEGER")
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON processing_jobs(user_id)"
            )
            await db.commit()
            print("✓ Added user_id column")
        else:
            print("✓ user_id column already exists")


async def init_database():
    """Initialize database with schema"""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Read and execute schema
        with open(SCHEMA_PATH, "r") as f:
            schema = f.read()

        await db.executescript(schema)
        await db.commit()

        print(f"Database initialized at {db_path}")


async def migrate_user_usage_tracking():
    """Add usage tracking columns to users table"""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Check if column exists
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "daily_requests" not in column_names:
            print("Adding daily_requests column to users table...")
            await db.execute(
                "ALTER TABLE users ADD COLUMN daily_requests INTEGER DEFAULT 0"
            )
            await db.execute("ALTER TABLE users ADD COLUMN last_request_date TEXT")
            await db.execute(
                "ALTER TABLE users ADD COLUMN is_limited BOOLEAN DEFAULT 0"
            )
            await db.commit()
            print("✓ Added usage tracking columns")
        else:
            print("✓ Usage tracking columns already exist")


async def migrate_user_id_to_uploaded_files():
    """Add user_id column to uploaded_files table"""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("PRAGMA table_info(uploaded_files)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "user_id" not in column_names:
            print("Adding user_id column to uploaded_files table...")
            await db.execute("ALTER TABLE uploaded_files ADD COLUMN user_id INTEGER")
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_uploaded_files_user_id ON uploaded_files(user_id)"
            )
            await db.commit()
            print("✓ Added user_id column to uploaded_files")
        else:
            print("✓ uploaded_files.user_id already exists")


async def migrate_guest_tokens():
    """Add guest ownership tokens to uploaded_files and processing_jobs."""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("PRAGMA table_info(uploaded_files)")
        uploaded_columns = [col[1] for col in await cursor.fetchall()]
        if "guest_token" not in uploaded_columns:
            print("Adding guest_token column to uploaded_files table...")
            await db.execute("ALTER TABLE uploaded_files ADD COLUMN guest_token TEXT")
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_uploaded_files_guest_token ON uploaded_files(guest_token)"
            )
            await db.commit()
            print("✓ Added uploaded_files.guest_token")
        else:
            print("✓ uploaded_files.guest_token already exists")

        cursor = await db.execute("PRAGMA table_info(processing_jobs)")
        job_columns = [col[1] for col in await cursor.fetchall()]
        if "guest_token" not in job_columns:
            print("Adding guest_token column to processing_jobs table...")
            await db.execute("ALTER TABLE processing_jobs ADD COLUMN guest_token TEXT")
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_guest_token ON processing_jobs(guest_token)"
            )
            await db.commit()
            print("✓ Added processing_jobs.guest_token")
        else:
            print("✓ processing_jobs.guest_token already exists")


async def migrate_job_metadata_column():
    """Add metadata column to processing_jobs table"""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("PRAGMA table_info(processing_jobs)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if "metadata" not in column_names:
            print("Adding metadata column to processing_jobs table...")
            await db.execute("ALTER TABLE processing_jobs ADD COLUMN metadata TEXT")
            await db.commit()
            print("✓ Added metadata column")
        else:
            print("✓ processing_jobs.metadata already exists")


async def migrate_cost_tracking_columns():
    """Add cost tracking columns to processing_jobs table"""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("PRAGMA table_info(processing_jobs)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        for col_name in [
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "estimated_cost",
        ]:
            if col_name not in column_names:
                print(f"Adding {col_name} column to processing_jobs table...")
                await db.execute(f"ALTER TABLE processing_jobs ADD COLUMN {col_name}")
                await db.commit()
                print(f"✓ Added {col_name} column")
            else:
                print(f"✓ processing_jobs.{col_name} already exists")


async def migrate_benchmark_tables():
    """Create benchmark_runs and benchmark_results tables"""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='benchmark_runs'"
        )
        result = await cursor.fetchone()

        if result is None:
            print("Creating benchmark_runs table...")
            await db.execute("""
                CREATE TABLE benchmark_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    sample_count INTEGER NOT NULL,
                    overall_accuracy REAL,
                    avg_latency REAL,
                    total_cost REAL,
                    total_prompt_tokens INTEGER,
                    total_completion_tokens INTEGER,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_benchmark_runs_dataset ON benchmark_runs(dataset)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_benchmark_runs_provider ON benchmark_runs(provider)"
            )
            await db.commit()
            print("✓ Created benchmark_runs table")
        else:
            print("✓ benchmark_runs table already exists")

        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='benchmark_results'"
        )
        result = await cursor.fetchone()

        if result is None:
            print("Creating benchmark_results table...")
            await db.execute("""
                CREATE TABLE benchmark_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    sample_index INTEGER NOT NULL,
                    file_path TEXT,
                    accuracy_score REAL,
                    latency REAL,
                    cost REAL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    expected_json TEXT,
                    actual_json TEXT,
                    field_scores TEXT,
                    error_message TEXT,
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE
                )
            """)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_benchmark_results_run_id ON benchmark_results(run_id)"
            )
            await db.commit()
            print("✓ Created benchmark_results table")
        else:
            print("✓ benchmark_results table already exists")


async def migrate_legacy_benchmark_data():
    """Import legacy benchmark data from backend/data if canonical DB has none."""
    db_path = _get_db_path()
    legacy_path = LEGACY_DB_PATH.resolve()
    if legacy_path == db_path or not legacy_path.exists():
        return

    async with aiosqlite.connect(legacy_path) as legacy_db:
        cursor = await legacy_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='benchmark_runs'"
        )
        if await cursor.fetchone() is None:
            return

        cursor = await legacy_db.execute("SELECT COUNT(*) FROM benchmark_runs")
        legacy_count = (await cursor.fetchone())[0]
        if legacy_count == 0:
            return

        legacy_db.row_factory = aiosqlite.Row
        runs_cursor = await legacy_db.execute(
            """
            SELECT id, dataset, provider, model, sample_count, overall_accuracy,
                   avg_latency, total_cost, total_prompt_tokens, total_completion_tokens,
                   started_at, completed_at
            FROM benchmark_runs
            ORDER BY id
            """
        )
        runs = await runs_cursor.fetchall()

        results_cursor = await legacy_db.execute(
            """
            SELECT id, run_id, sample_index, file_path, accuracy_score, latency, cost,
                   prompt_tokens, completion_tokens, expected_json, actual_json,
                   field_scores, error_message
            FROM benchmark_results
            ORDER BY id
            """
        )
        results = await results_cursor.fetchall()

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM benchmark_runs")
        current_count = (await cursor.fetchone())[0]
        if current_count > 0:
            print("✓ canonical benchmark data already present")
            return

        try:
            run_id_map: dict[int, int] = {}
            for run in runs:
                cursor = await db.execute(
                    """
                    INSERT INTO benchmark_runs (
                        dataset, provider, model, sample_count, overall_accuracy,
                        avg_latency, total_cost, total_prompt_tokens, total_completion_tokens,
                        started_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run["dataset"],
                        run["provider"],
                        run["model"],
                        run["sample_count"],
                        run["overall_accuracy"],
                        run["avg_latency"],
                        run["total_cost"],
                        run["total_prompt_tokens"],
                        run["total_completion_tokens"],
                        run["started_at"],
                        run["completed_at"],
                    ),
                )
                run_id_map[run["id"]] = cursor.lastrowid

            for result in results:
                mapped_run_id = run_id_map.get(result["run_id"])
                if mapped_run_id is None:
                    continue
                await db.execute(
                    """
                    INSERT INTO benchmark_results (
                        run_id, sample_index, file_path, accuracy_score, latency, cost,
                        prompt_tokens, completion_tokens, expected_json, actual_json,
                        field_scores, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        mapped_run_id,
                        result["sample_index"],
                        result["file_path"],
                        result["accuracy_score"],
                        result["latency"],
                        result["cost"],
                        result["prompt_tokens"],
                        result["completion_tokens"],
                        result["expected_json"],
                        result["actual_json"],
                        result["field_scores"],
                        result["error_message"],
                    ),
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    print(f"✓ Imported {legacy_count} benchmark runs from legacy backend/data database")


async def migrate_quality_gate():
    """Add quality gate columns to processing_jobs table"""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("PRAGMA table_info(processing_jobs)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        for col_name in ["quality_score", "quality_checks", "preprocessing_applied"]:
            if col_name not in column_names:
                print(f"Adding {col_name} column to processing_jobs table...")
                await db.execute(f"ALTER TABLE processing_jobs ADD COLUMN {col_name}")
                await db.commit()
                print(f"✓ Added {col_name} column")
            else:
                print(f"✓ processing_jobs.{col_name} already exists")


async def migrate_phase23_tables():
    """Add Phase 2/3 columns and tables."""
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("PRAGMA table_info(processing_jobs)")
        job_columns = [col[1] for col in await cursor.fetchall()]

        if "document_type" not in job_columns:
            print("Adding document_type column to processing_jobs table...")
            await db.execute(
                "ALTER TABLE processing_jobs ADD COLUMN document_type TEXT"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_document_type ON processing_jobs(document_type)"
            )
            await db.commit()
            print("✓ Added processing_jobs.document_type")
        else:
            print("✓ processing_jobs.document_type already exists")

        if "correction_status" not in job_columns:
            print("Adding correction_status column to processing_jobs table...")
            await db.execute(
                "ALTER TABLE processing_jobs ADD COLUMN correction_status TEXT DEFAULT 'uncorrected'"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_correction_status ON processing_jobs(correction_status)"
            )
            await db.commit()
            print("✓ Added processing_jobs.correction_status")
        else:
            print("✓ processing_jobs.correction_status already exists")

        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_suggestions'"
        )
        if await cursor.fetchone() is None:
            print("Creating schema_suggestions table...")
            await db.execute(
                """
                CREATE TABLE schema_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_ids TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    document_type TEXT,
                    draft_name TEXT,
                    schema_definition TEXT NOT NULL,
                    field_descriptions TEXT,
                    rationale TEXT,
                    confidence REAL,
                    status TEXT DEFAULT 'draft',
                    created_by_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
                )
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_schema_suggestions_created_by ON schema_suggestions(created_by_user_id)"
            )
            await db.commit()
            print("✓ Created schema_suggestions table")
        else:
            print("✓ schema_suggestions table already exists")

        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='job_corrections'"
        )
        if await cursor.fetchone() is None:
            print("Creating job_corrections table...")
            await db.execute(
                """
                CREATE TABLE job_corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    original_result TEXT NOT NULL,
                    corrected_result TEXT NOT NULL,
                    diff_summary TEXT,
                    feedback_tags TEXT,
                    notes TEXT,
                    reviewer_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES processing_jobs(id) ON DELETE CASCADE,
                    FOREIGN KEY (reviewer_user_id) REFERENCES users(id) ON DELETE SET NULL
                )
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_job_corrections_job_id ON job_corrections(job_id)"
            )
            await db.commit()
            print("✓ Created job_corrections table")
        else:
            print("✓ job_corrections table already exists")

        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_learning_entries'"
        )
        if await cursor.fetchone() is None:
            print("Creating prompt_learning_entries table...")
            await db.execute(
                """
                CREATE TABLE prompt_learning_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schema_name TEXT,
                    provider TEXT,
                    model TEXT,
                    processing_method TEXT,
                    entry_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_correction_count INTEGER DEFAULT 0,
                    last_correction_id INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (last_correction_id) REFERENCES job_corrections(id) ON DELETE SET NULL
                )
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_prompt_learning_schema_name ON prompt_learning_entries(schema_name)"
            )
            await db.commit()
            print("✓ Created prompt_learning_entries table")
        else:
            print("✓ prompt_learning_entries table already exists")


async def run_migrations():
    """Run all database migrations"""
    db_path = _get_db_path()
    if not db_path.exists():
        await init_database()
    await migrate_processing_method()
    await migrate_users_table()
    await migrate_user_id_to_jobs()
    await migrate_user_usage_tracking()
    await migrate_user_id_to_uploaded_files()
    await migrate_guest_tokens()
    await migrate_job_metadata_column()
    await migrate_cost_tracking_columns()
    await migrate_benchmark_tables()
    await migrate_legacy_benchmark_data()
    await migrate_quality_gate()
    await migrate_phase23_tables()
    print("All migrations completed successfully")


if __name__ == "__main__":
    asyncio.run(run_migrations())

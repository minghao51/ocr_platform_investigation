import aiosqlite
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Awaitable
from paths import get_db_path

logger = logging.getLogger(__name__)
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


@dataclass
class Migration:
    name: str
    up: Callable[[aiosqlite.Connection], Awaitable[None]]


async def _check_column(db: aiosqlite.Connection, table: str, column: str) -> bool:
    cursor = await db.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in await cursor.fetchall()]
    return column in columns


async def _check_table(db: aiosqlite.Connection, table: str) -> bool:
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return await cursor.fetchone() is not None


async def _add_column(
    db: aiosqlite.Connection,
    table: str,
    column: str,
    col_type: str = "",
    create_index: bool = False,
) -> None:
    if await _check_column(db, table, column):
        logger.debug("%s.%s already exists", table, column)
        return
    logger.info("Adding %s column to %s table", column, table)
    sql = f"ALTER TABLE {table} ADD COLUMN {column}"
    if col_type:
        sql += f" {col_type}"
    await db.execute(sql)
    if create_index:
        await db.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table}_{column} ON {table}({column})"
        )
    await db.commit()


async def _add_columns(
    db: aiosqlite.Connection,
    table: str,
    columns: list[tuple[str, str]],
    create_indexes: bool = False,
) -> None:
    for col_name, col_type in columns:
        await _add_column(db, table, col_name, col_type, create_indexes)


async def _init_database(db: aiosqlite.Connection) -> None:
    if await _check_table(db, "processing_jobs"):
        return
    logger.info("Initializing database from schema.sql")
    with open(SCHEMA_PATH) as f:
        await db.executescript(f.read())
    await db.commit()


async def _migrate_users_table(db: aiosqlite.Connection) -> None:
    if await _check_table(db, "users"):
        return
    logger.info("Creating users table")
    await db.execute(
        """CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            token_version INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    await db.commit()


async def _migrate_benchmark_tables(db: aiosqlite.Connection) -> None:
    if not await _check_table(db, "benchmark_runs"):
        logger.info("Creating benchmark_runs table")
        await db.execute(
            """CREATE TABLE benchmark_runs (
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
            )"""
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_benchmark_runs_dataset ON benchmark_runs(dataset)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_benchmark_runs_provider ON benchmark_runs(provider)"
        )
        await db.commit()

    if not await _check_table(db, "benchmark_results"):
        logger.info("Creating benchmark_results table")
        await db.execute(
            """CREATE TABLE benchmark_results (
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
            )"""
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_benchmark_results_run_id ON benchmark_results(run_id)"
        )
        await db.commit()

    await _add_column(db, "benchmark_runs", "processing_method", "TEXT")


async def _migrate_schema_suggestions(db: aiosqlite.Connection) -> None:
    if await _check_table(db, "schema_suggestions"):
        return
    logger.info("Creating schema_suggestions table")
    await db.execute(
        """CREATE TABLE schema_suggestions (
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
        )"""
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_schema_suggestions_created_by ON schema_suggestions(created_by_user_id)"
    )
    await db.commit()


async def _migrate_job_corrections(db: aiosqlite.Connection) -> None:
    if await _check_table(db, "job_corrections"):
        return
    logger.info("Creating job_corrections table")
    await db.execute(
        """CREATE TABLE job_corrections (
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
        )"""
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_job_corrections_job_id ON job_corrections(job_id)"
    )
    await db.commit()


async def _migrate_prompt_learning(db: aiosqlite.Connection) -> None:
    if await _check_table(db, "prompt_learning_entries"):
        return
    logger.info("Creating prompt_learning_entries table")
    await db.execute(
        """CREATE TABLE prompt_learning_entries (
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
        )"""
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_prompt_learning_schema_name ON prompt_learning_entries(schema_name)"
    )
    await db.commit()


async def _migrate_job_queue(db: aiosqlite.Connection) -> None:
    if await _check_table(db, "job_queue"):
        return
    logger.info("Creating job_queue table")
    await db.execute(
        """CREATE TABLE job_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL UNIQUE,
            task_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            payload TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            worker_id TEXT,
            locked_at TIMESTAMP,
            last_error TEXT,
            run_after TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES processing_jobs(id) ON DELETE CASCADE
        )"""
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_job_queue_run_after ON job_queue(run_after)"
    )
    await db.commit()


MIGRATIONS: list[Migration] = [
    Migration("init_database", _init_database),
    Migration("users_table", _migrate_users_table),
    Migration("processing_method_column",
              lambda db: _add_column(db, "processing_jobs", "processing_method", "TEXT DEFAULT 'vision'", True)),
    Migration("user_id_to_jobs",
              lambda db: _add_column(db, "processing_jobs", "user_id", "INTEGER", True)),
    Migration("user_usage_tracking",
              lambda db: _add_columns(db, "users", [
                  ("daily_requests", "INTEGER DEFAULT 0"),
                  ("last_request_date", "TEXT"),
                  ("is_limited", "BOOLEAN DEFAULT 0"),
              ])),
    Migration("user_token_version",
              lambda db: _add_column(db, "users", "token_version", "INTEGER DEFAULT 0")),
    Migration("user_id_to_uploaded_files",
              lambda db: _add_column(db, "uploaded_files", "user_id", "INTEGER", True)),
    Migration("guest_tokens_uploaded_files",
              lambda db: _add_column(db, "uploaded_files", "guest_token", "TEXT", True)),
    Migration("guest_tokens_processing_jobs",
              lambda db: _add_column(db, "processing_jobs", "guest_token", "TEXT", True)),
    Migration("job_metadata_column",
              lambda db: _add_column(db, "processing_jobs", "metadata", "TEXT")),
    Migration("cost_tracking_columns",
              lambda db: _add_columns(db, "processing_jobs", [
                  ("prompt_tokens", ""),
                  ("completion_tokens", ""),
                  ("total_tokens", ""),
                  ("estimated_cost", ""),
              ])),
    Migration("benchmark_tables", _migrate_benchmark_tables),
    Migration("benchmark_results_peak_memory",
              lambda db: _add_column(db, "benchmark_results", "peak_memory_mb", "REAL")),
    Migration("quality_gate_columns",
              lambda db: _add_columns(db, "processing_jobs", [
                  ("quality_score", ""),
                  ("quality_checks", ""),
                  ("preprocessing_applied", ""),
              ])),
    Migration("phase23_document_type",
              lambda db: _add_column(db, "processing_jobs", "document_type", "TEXT", True)),
    Migration("phase23_correction_status",
              lambda db: _add_column(db, "processing_jobs", "correction_status", "TEXT DEFAULT 'uncorrected'", True)),
    Migration("phase23_schema_suggestions", _migrate_schema_suggestions),
    Migration("phase23_job_corrections", _migrate_job_corrections),
    Migration("phase23_prompt_learning", _migrate_prompt_learning),
    Migration("job_queue", _migrate_job_queue),
]


async def run_migrations() -> None:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        for migration in MIGRATIONS:
            try:
                await migration.up(db)
            except Exception:
                logger.exception("Migration '%s' failed", migration.name)
                raise

    logger.info("All migrations completed successfully")


if __name__ == "__main__":
    asyncio.run(run_migrations())

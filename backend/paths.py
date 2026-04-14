from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "ocr_platform.db"
UPLOAD_DIR = DATA_DIR / "uploads"
BENCHMARKS_DIR = DATA_DIR / "benchmarks"


def get_db_path() -> Path:
    """Get database path from settings URL. Only SQLite is supported."""
    from config import get_settings

    database_url = get_settings().database_url
    if not database_url.startswith("sqlite:///"):
        raise ValueError(f"Only SQLite databases are supported. Got: {database_url}")
    return Path(database_url.removeprefix("sqlite:///")).resolve()


# Legacy path for data migration from old backend/ cwd structure.
# TODO: Remove after 2026-06-01 once all users have migrated to /data layout.
LEGACY_BACKEND_DATA_DIR = BACKEND_DIR / "data"
LEGACY_DB_PATH = LEGACY_BACKEND_DATA_DIR / "ocr_platform.db"

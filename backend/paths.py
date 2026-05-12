from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent

if not (REPO_ROOT / "data").exists() and (Path("/app/data")).exists():
    REPO_ROOT = Path("/app")

DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "ocr_platform.db"
UPLOAD_DIR = DATA_DIR / "uploads"
BENCHMARKS_DIR = DATA_DIR / "benchmarks"


def get_db_path() -> Path:
    from config import get_settings

    database_url = get_settings().database_url
    if not database_url.startswith("sqlite:///"):
        raise ValueError(f"Only SQLite databases are supported. Got: {database_url}")
    return Path(database_url.removeprefix("sqlite:///")).resolve()

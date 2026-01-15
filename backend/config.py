from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    nebius_api_key: str = ""
    openrouter_api_key: str = ""
    gemini_api_key: str = ""

    database_url: str = "sqlite:///./data/ocr_platform.db"

    max_file_size: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()

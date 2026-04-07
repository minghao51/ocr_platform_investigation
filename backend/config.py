from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
from paths import DB_PATH


class Settings(BaseSettings):
    # VLM Provider API Keys
    nebius_api_key: str = ""
    openrouter_api_key: str = ""
    gemini_api_key: str = ""

    # Database
    database_url: str = f"sqlite:///{DB_PATH}"

    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # CORS Origins (comma-separated list, will be parsed into list)
    cors_origins_str: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [
            origin.strip()
            for origin in self.cors_origins_str.split(",")
            if origin.strip()
        ]

    # JWT Authentication
    jwt_secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Rate Limiting
    rate_limit_per_minute: int = 10

    class Config:
        env_file = "../.env"
        extra = "ignore"


@lru_cache
def get_settings():
    return Settings()

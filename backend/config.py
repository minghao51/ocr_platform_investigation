from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
from paths import DB_PATH


class Settings(BaseSettings):
    # VLM Provider API Keys
    openrouter_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Database
    database_url: str = f"sqlite:///{DB_PATH}"

    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # CORS Origins (comma-separated list, will be parsed into list)
    cors_origins_str: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        validation_alias=AliasChoices("CORS_ORIGINS_STR", "CORS_ORIGINS"),
    )

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
    # General API rate limit: 10 requests per minute (applies to all users via slowapi)
    rate_limit_per_minute: int = 10

    # Demo user daily limit: 5 requests per day (for is_limited users)
    # This is a separate cap that applies in addition to per-minute limits
    demo_daily_request_limit: int = 5

    @model_validator(mode="before")
    @classmethod
    def ignore_encrypted_dotenv_values(cls, data):
        """
        Allow local `uv run ...` usage even when `.env` contains dotenvx-encrypted
        placeholders by treating undecrypted values as missing and falling back to
        defaults/environment overrides.
        """
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("encrypted:"):
                continue
            sanitized[key] = value
        return sanitized

    class Config:
        env_file = "../.env"
        extra = "ignore"


@lru_cache
def get_settings():
    return Settings()

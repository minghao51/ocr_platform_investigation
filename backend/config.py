import logging
from pydantic import AliasChoices, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
from paths import DB_PATH

_DEFAULT_JWT_SECRET = "change-me-in-production-use-openssl-rand-hex-32"

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = ConfigDict(env_file="../.env", extra="ignore")

    openrouter_api_key: str = ""
    gemini_api_key: str = ""

    database_url: str = f"sqlite:///{DB_PATH}"

    max_file_size: int = 10 * 1024 * 1024  # 10MB
    docling_parse_timeout_seconds: int = 60

    cors_origins_str: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        validation_alias=AliasChoices("CORS_ORIGINS_STR", "CORS_ORIGINS"),
    )

    @property
    def cors_origins(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.cors_origins_str.split(",")
            if origin.strip()
        ]

    jwt_secret_key: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT", "ENV"),
    )

    rate_limit_per_minute: int = 10
    demo_daily_request_limit: int = 5
    enable_job_worker: bool = True

    @property
    def is_using_default_jwt_secret(self) -> bool:
        return self.jwt_secret_key == _DEFAULT_JWT_SECRET

    @property
    def is_local_environment(self) -> bool:
        env = self.environment.strip().lower()
        return env in {"dev", "development", "local", "test"}

    @model_validator(mode="before")
    @classmethod
    def ignore_encrypted_dotenv_values(cls, data):
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("encrypted:"):
                continue
            sanitized[key] = value
        return sanitized

@lru_cache
def get_settings():
    settings = Settings()
    if settings.is_using_default_jwt_secret:
        if settings.is_local_environment:
            logger.warning(
                "JWT secret key is set to the default value. "
                "Set JWT_SECRET_KEY env var for production deployments."
            )
        else:
            raise RuntimeError(
                "JWT secret key is set to the default value in a non-local environment. "
                "Set JWT_SECRET_KEY before starting the application."
            )
    return settings

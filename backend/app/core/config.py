from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Reads config from env vars / .env; field names map case-insensitively."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./dev_journal.db"
    anthropic_api_key: str | None = None  # none until Phase 3
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()

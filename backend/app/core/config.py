from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# BaseSettings is a Pydantic class that allows you to define settings for your application. It can read from environment variables, .env files, and other sources. The SettingsConfigDict is used to configure the behavior of the BaseSettings class, such as specifying the location of the .env file and its encoding.
# field names map to env vars case-insensitively (anthropic_api_key <- ANTHROPIC_API_KEY)
# Default means nothing crashes if .env doesn't exist yet. 
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./dev_journal.db"
    anthropic_api_key: str | None = None # none until Phase 3
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()

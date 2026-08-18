from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEV_JOURNAL_")
    api_url: str = "http://127.0.0.1:8000" # where the backend runs locally

@lru_cache()
def get_settings() -> Settings:
    return Settings()

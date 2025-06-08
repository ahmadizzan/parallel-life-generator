from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables and .env files."""

    OPENAI_API_KEY: SecretStr
    LLM_PROVIDER: str = "openai"
    MODEL_NAME: str = "gpt-4-turbo-preview"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    return Settings()  # type: ignore[call-arg]

"""Application configuration utilities."""

from functools import cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = Field(alias='DATABASE_URL')

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


@cache
def get_settings() -> Settings:
    """Return cached application settings.

    Returns:
        Settings: Application settings loaded from environment variables.
    """
    return Settings()

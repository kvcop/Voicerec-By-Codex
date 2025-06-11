"""Application configuration utilities."""

from functools import cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = Field(alias='DATABASE_URL')
    gpu_grpc_host: str = Field(alias='GPU_GRPC_HOST')
    gpu_grpc_port: int = Field(alias='GPU_GRPC_PORT')
    gpu_grpc_use_tls: bool = Field(False, alias='GPU_GRPC_USE_TLS')
    gpu_grpc_tls_ca: str | None = Field(None, alias='GPU_GRPC_TLS_CA')
    gpu_grpc_tls_cert: str | None = Field(None, alias='GPU_GRPC_TLS_CERT')
    gpu_grpc_tls_key: str | None = Field(None, alias='GPU_GRPC_TLS_KEY')

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


@cache
def get_settings() -> Settings:
    """Return cached application settings.

    Returns:
        Settings: Application settings loaded from environment variables.
    """
    return Settings()

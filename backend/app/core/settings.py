"""Application configuration utilities."""

from functools import cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GPUSettings(BaseSettings):
    """Configuration for GPU node connection."""

    grpc_host: str = Field(
        description='GPU node gRPC host name',
    )
    grpc_port: int = Field(
        description='Port of the gRPC service',
    )
    grpc_use_tls: bool = Field(
        False,
        description='Enable TLS for the gRPC channel',
    )
    grpc_tls_ca: str | None = Field(
        None,
        description='Path to the CA certificate file',
    )
    grpc_tls_cert: str | None = Field(
        None,
        description='Path to the client certificate file',
    )
    grpc_tls_key: str | None = Field(
        None,
        description='Path to the client private key',
    )

    @model_validator(mode='after')
    def _check_tls(self: 'GPUSettings') -> 'GPUSettings':
        """Ensure certificate paths are provided when TLS is enabled."""
        if self.grpc_use_tls and not all([self.grpc_tls_ca, self.grpc_tls_cert, self.grpc_tls_key]):
            message = 'TLS enabled but certificate paths are missing'
            raise ValueError(message)
        return self

    model_config = SettingsConfigDict(
        env_prefix='GPU_',
        env_file='.env',
        env_file_encoding='utf-8',
    )


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = Field(
        alias='DATABASE_URL',
        description='Database connection string',
    )
    gpu: GPUSettings = GPUSettings()

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


@cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

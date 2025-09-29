"""Application configuration utilities."""

from functools import cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RAW_AUDIO_DIR = REPO_ROOT / 'data' / 'raw'
DEFAULT_DATABASE_SCHEMA_VERSION = '0.1.0'


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
    database_schema_version: str = Field(
        default=DEFAULT_DATABASE_SCHEMA_VERSION,
        alias='DATABASE_SCHEMA_VERSION',
        description='Expected Alembic schema version for runtime validation',
    )
    raw_audio_dir: Path = Field(
        default=DEFAULT_RAW_AUDIO_DIR,
        alias='RAW_AUDIO_DIR',
        description='Directory for storing raw meeting audio files',
    )
    asr_model_size: str = Field(
        default='large-v2',
        alias='ASR_MODEL_SIZE',
        description='Whisper model size used by the GPU ASR service',
    )
    gpu: GPUSettings = Field(default_factory=GPUSettings)
    auth_secret_key: str = Field(
        alias='AUTH_SECRET_KEY',
        description='Secret key used to sign JWT access tokens',
        min_length=16,
    )
    auth_token_algorithm: str = Field(
        default='HS256',
        alias='AUTH_TOKEN_ALGORITHM',
        description='Algorithm employed to sign JWT access tokens',
    )
    auth_token_expire_minutes: int = Field(
        default=60,
        alias='AUTH_TOKEN_EXPIRE_MINUTES',
        description='Lifetime of JWT access tokens in minutes',
        ge=1,
    )

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


@cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

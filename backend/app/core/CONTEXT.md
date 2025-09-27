<<<<<< codex/2025-09-27-analyze-and-complete-task-s1
# Core Services Documentation

## Core Architecture
The core module provides configuration management, utility functions, and cross-cutting concerns for the backend application. It implements the foundation for settings, logging, security, and shared business logic.

### Responsibilities
- **Configuration**: Type-safe settings via Pydantic
- **Security**: Authentication, authorization, encryption
- **Utilities**: Logging, validation, helpers
- **Constants**: Shared enums and constants

## Configuration Management

### Settings Pattern
```python
class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Database configuration
    database_url: PostgresDsn
    pool_size: int = Field(default=20, ge=1, le=100)
    
    # Security settings
    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire: int = 30  # minutes
    
    # Feature flags
    enable_gpu_processing: bool = False
    mock_external_services: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
```

### GPU Settings
The `GPUSettings` class manages GPU node connection configuration:
- **gRPC connection**: Host, port, TLS settings
- **Certificate validation**: Ensures all certs provided when TLS enabled
- **Environment prefix**: `GPU_` for all GPU-related settings
- **Type safety**: Pydantic validation for all fields

### Environment Management
```python
# Development
DATABASE_URL=postgresql+asyncpg://dev:dev@localhost/dev
MOCK_EXTERNAL_SERVICES=true

# Production
DATABASE_URL=postgresql+asyncpg://prod:${DB_PASS}@db.prod/app
GPU_GRPC_USE_TLS=true
GPU_GRPC_TLS_CA=/certs/ca.pem
```

## Service Patterns

### Base Service Class
```python
class BaseService:
    """Common service functionality."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> Logger:
        """Configure structured logging."""
        return structlog.get_logger(
            service=self.__class__.__name__
        )
```

### Dependency Injection
```python
# Service factory pattern
def get_transcript_service(
    session: AsyncSession = Depends(get_session),
    client_type: str | None = None,
) -> TranscriptService:
    transcribe_client = build_transcribe_client(client_type)
    diarize_client = build_diarize_client(client_type)
    summarize_client = build_summarize_client(client_type)
    processor = MeetingProcessingService(transcribe_client, diarize_client, summarize_client)
    return TranscriptService(session, processor)
```

## Security Utilities

### Password Hashing (Future)
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### JWT Tokens (Future)
```python
def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```
=======
# Core Module Context

## Responsibilities
The `app.core` package centralizes configuration and cross-cutting utilities
for the backend:
- `settings.py` exposes typed Pydantic settings (`AppSettings`, `GPUSettings`).
- `logging.py` configures structured Loguru output and guards against
  duplicate initialization.
- `config.py` and helper modules define reusable constants and validation
  helpers shared across services.

## Settings Overview
- `DATABASE_URL` drives the async SQLAlchemy engine creation.
- `RAW_AUDIO_DIR` controls where uploaded WAV files are persisted. When missing,
  the service defaults to `<repo>/data/raw` and creates the folder lazily.
- GPU-related variables (prefixed with `GPU_`) are grouped in `GPUSettings`
  and reused by mocked gRPC client factories.
- Settings instances are cached via `functools.lru_cache` so tests can clear the
  cache after mutating environment variables.
>>>>>> main

## Logging Configuration
- `configure_logging()` removes default Loguru handlers and installs a single
  JSON sink bound to `sys.stdout`.
- Log level is configurable through the `LOG_LEVEL` environment variable.
- The function is idempotent and can be safely invoked multiple times (e.g., in
  tests or within `app.main`).

## Interaction With Other Layers
- `app.main` imports `configure_logging()` to activate logging before creating
  the FastAPI app and registers HTTP middleware that enriches Loguru records with
  method, path, query string, status code, and elapsed time.
- Dependency providers from `settings.py` are consumed by repositories,
  services, and tests to obtain consistent configuration objects.

## Testing Notes
- Tests relying on temporary databases call `get_settings.cache_clear()` via the
  `reset_engine_cache()` helper to pick up modified URLs.
- Logging configuration remains active during tests; Loguru sinks can be patched
  with `logger.add()` where needed.

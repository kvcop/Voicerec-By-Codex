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

## Logging Configuration

### Structured Logging
```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

### Request Logging
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    with structlog.contextvars.bound_contextvars(
        request_id=request_id
    ):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            "request_processed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=process_time
        )
    return response
```

## Validation Utilities

### Custom Validators
```python
def validate_audio_file(file: UploadFile) -> None:
    """Validate audio file format and size."""
    ALLOWED_TYPES = {"audio/wav", "audio/mp3", "audio/ogg"}
    MAX_SIZE = 500 * 1024 * 1024  # 500MB
    
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError(f"Invalid type: {file.content_type}")
    
    if file.size > MAX_SIZE:
        raise ValueError(f"File too large: {file.size}")
```

### Business Rule Validation
```python
class MeetingValidator:
    @staticmethod
    def validate_duration(duration: int) -> None:
        if duration < 60:
            raise ValueError("Meeting too short")
        if duration > 14400:  # 4 hours
            raise ValueError("Meeting too long")
```

## Constants and Enums

### Status Enums
```python
from enum import Enum

class TranscriptStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SpeakerRole(str, Enum):
    HOST = "host"
    PARTICIPANT = "participant"
    GUEST = "guest"
```

### Configuration Constants
```python
# File handling
CHUNK_SIZE = 1024 * 1024  # 1MB chunks
TEMP_DIR = Path("/tmp/voicerec")
AUDIO_STORAGE = Path("data/raw")

# Processing limits
MAX_CONCURRENT_JOBS = 10
JOB_TIMEOUT = 3600  # 1 hour
RETRY_ATTEMPTS = 3
```

## Error Handling

### Custom Exceptions
```python
class CoreException(Exception):
    """Base exception for core errors."""
    pass

class ConfigurationError(CoreException):
    """Invalid configuration."""
    pass

class ValidationError(CoreException):
    """Business rule violation."""
    pass
```

## Utility Functions

### Time Utilities
```python
def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)

def format_duration(seconds: int) -> str:
    """Format seconds as HH:MM:SS."""
    return str(timedelta(seconds=seconds))
```

### File Utilities
```python
async def save_upload(
    file: UploadFile,
    destination: Path
) -> None:
    """Save uploaded file asynchronously."""
    async with aiofiles.open(destination, 'wb') as f:
        while content := await file.read(CHUNK_SIZE):
            await f.write(content)
```

## Testing Helpers

### Test Fixtures
```python
@pytest.fixture
def test_settings():
    """Override settings for tests."""
    return Settings(
        database_url="postgresql+asyncpg://test:test@localhost/test",
        mock_external_services=True,
        gpu_grpc_host="mock.gpu.local"
    )
```

## Performance Monitoring (Future)

### Metrics Collection
```python
from prometheus_client import Counter, Histogram

request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)
```

---

*This documentation covers core services and utilities. Update when adding new core functionality or changing patterns.*
# Backend - Component Context

## Purpose
FastAPI-based backend service providing APIs for audio upload, transcript streaming, and meeting management. Integrates with GPU nodes for ML processing (ASR, speaker identification, summarization) via secure gRPC connections.

## Current Status: Active Development
The backend is in active development with core infrastructure established. Audio upload and SSE streaming endpoints are implemented. GPU service integration uses factory pattern with mocked services for development. Database models and repository pattern pending implementation.

## Component-Specific Development Guidelines

### Python Standards
- **Python 3.13+** with type hints on all functions
- **Async/await** for all I/O operations
- **Google-style docstrings** in English
- Functions with >2 args require `Args` section
- Complex returns need `Returns` section
- Explicit exceptions need `Raises` section

### FastAPI Patterns
- **Thin endpoints** - Business logic in service classes
- **Dependency injection** for services and repositories
- **Pydantic models** for request/response validation
- **Background tasks** for async processing

### Database Patterns
- **Repository pattern** mandatory (in `app/database/repositories/`)
- **AsyncSession** for all database operations
- **SQLAlchemy 2.0** declarative models
- **Alembic** for migrations (future)

### Testing Requirements
- **pytest** with async support
- **Mock gRPC clients** via factory pattern
- **Test fixtures** for database and services
- **100% endpoint coverage** expected

## Major Subsystem Organization

### API Layer (`app/api/`)
- **meeting.py**: Audio upload, SSE transcript streaming
- Future: authentication, user management, analytics

### Core Configuration (`app/core/`)
- **settings.py**: Pydantic settings with GPU/DB configuration
- Environment-based config via `.env` files
- Type-safe configuration validation
- **logging.py**: Configures Loguru with JSON output and HTTP middleware bindings

### Database Layer (`app/db/`)
- **session.py**: AsyncSession factory
- **models/**: SQLAlchemy model definitions (pending)
- **repositories/**: Repository pattern implementations (pending)

### Integration Layer
- **grpc_client.py**: Factory pattern for GPU service clients
- Mock implementations for development
- TLS/mTLS support for production

## Architectural Patterns

### Service Layer Pattern
```python
# Endpoint (thin controller)
@router.post("/upload")
async def upload_audio(
    file: UploadFile,
    service: AudioService = Depends(get_audio_service)
):
    return await service.process_upload(file)

# Service (business logic)
class AudioService:
    def __init__(self, repo: AudioRepository, gpu_client: GRPCClient):
        self.repo = repo
        self.gpu_client = gpu_client
    
    async def process_upload(self, file: UploadFile):
        # Business logic here
        pass
```

### Repository Pattern
```python
class MeetingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, meeting_data: dict) -> Meeting:
        # Database operations only
        pass
```

### gRPC Client Factory
```python
def create_grpc_client(settings: GPUSettings) -> GRPCClientProtocol:
    if settings.mock_mode:
        return MockGRPCClient()
    return ProductionGRPCClient(settings)
```

## Integration Points

### External Services
- **PostgreSQL**: Primary data store via asyncpg
- **GPU Node**: ML services via gRPC (ASR, speaker, summarizer)
- **Frontend**: RESTful APIs and SSE streaming

### Security Requirements
- **mTLS/VPN** for GPU communication
- **TLS certificates** validated via GPUSettings
- **Environment variables** for sensitive configuration
- **No secrets in code** - use .env files

### Performance Considerations
- **Async everywhere** - No blocking I/O
- **Connection pooling** for database
- **Streaming responses** for large data
- **Background tasks** for heavy processing

## Error Handling Strategy

### Validation Errors
- Pydantic automatic validation
- 422 status with detailed error messages

### Service Errors
- Custom exception classes
- Proper HTTP status codes
- Structured error responses

### Integration Failures
- Circuit breaker pattern (future)
- Graceful degradation
- Retry with exponential backoff

## Development Commands

All commands run from `backend/` directory:

```bash
# Setup
uv sync

# Development
uv run uvicorn app.main:app --reload

## Observability

- Structured JSON logging via Loguru configured in `app/core/logging.py`
- Automatic HTTP request/response logging through FastAPI middleware

# Quality checks (in order)
uv run ruff check --fix .
uv run ruff format .
uv run mypy .

# Testing
uv run pytest
uv run pytest tests/test_meeting.py -v  # Specific test

# Database (future)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

## Key Files Reference

- **app/main.py**: FastAPI application initialization
- **app/core/settings.py**: Configuration management
- **app/api/meeting.py**: Core API endpoints
- **app/grpc_client.py**: GPU service integration
- **app/db/session.py**: Database session management

## Next Implementation Steps

1. SQLAlchemy models for meetings, transcripts, users
2. Repository implementations for data access
3. Service layer for business logic
4. Authentication/authorization middleware
5. WebSocket support for real-time updates
6. Comprehensive error handling
7. Monitoring and logging setup

---

*This component documentation provides architectural context for the backend service. Update when patterns evolve or new subsystems are added.*
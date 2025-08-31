# API Layer Documentation

## API Architecture
The API layer implements RESTful endpoints and Server-Sent Events (SSE) for real-time streaming. All endpoints follow FastAPI patterns with automatic OpenAPI documentation, type validation via Pydantic, and dependency injection for services.

### Core Principles
- **Thin controllers**: Endpoints delegate to service layer
- **Type safety**: Pydantic models for all I/O
- **Async first**: All operations are async
- **Dependency injection**: Services injected via Depends()

## Implementation Patterns

### Endpoint Structure
```python
@router.post("/resource", response_model=ResponseModel)
async def create_resource(
    data: RequestModel,
    service: ResourceService = Depends(get_service),
    db: AsyncSession = Depends(get_session)
) -> ResponseModel:
    """Endpoint docstring for OpenAPI."""
    return await service.create(data, db)
```

### File Upload Pattern
```python
@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    meeting_id: str = Form(...)
):
    # Validate file type
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(400, "Invalid file type")
    
    # Stream to storage
    async with aiofiles.open(path, 'wb') as f:
        while chunk := await file.read(CHUNK_SIZE):
            await f.write(chunk)
```

### SSE Streaming Pattern
```python
async def event_generator(meeting_id: str):
    """Generate SSE events for transcript streaming."""
    async for transcript in service.stream_transcript(meeting_id):
        yield f"data: {json.dumps(transcript)}\n\n"
    yield "event: end\ndata: {}\n\n"
```

## Error Handling Strategies

### Validation Errors
- Automatic 422 with field details via Pydantic
- Custom validators for business rules

### Business Logic Errors
```python
class MeetingNotFoundError(HTTPException):
    def __init__(self, meeting_id: str):
        super().__init__(
            status_code=404,
            detail=f"Meeting {meeting_id} not found"
        )
```

### Integration Errors
- 503 for external service failures
- Retry logic in service layer
- Circuit breaker pattern (future)

## Key Files and Structure

### Current Endpoints
- **meeting.py**: Audio upload, transcript streaming
  - `POST /api/meeting/upload` - Upload audio file
  - `GET /api/meeting/{id}/stream` - SSE transcript stream
  - `GET /api/meeting/{id}` - Get meeting details (future)

### Future Endpoints
- **auth.py**: Authentication/authorization
- **user.py**: User management
- **analytics.py**: Usage analytics
- **admin.py**: Administrative functions

## Integration Points

### Service Layer
- Endpoints inject services via Depends()
- Services handle all business logic
- Clean separation of concerns

### Database Layer
- Sessions injected via Depends(get_session)
- Transactions managed by service layer
- No direct DB access in endpoints

### External Services
- gRPC clients injected via factory
- Async HTTP clients for webhooks
- Message queues for async processing (future)

## Security Considerations

### Authentication (Future)
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
    # JWT validation
    # User lookup
    # Permission check
```

### Rate Limiting (Future)
- Per-user limits
- Endpoint-specific limits
- Redis-backed counters

### Input Validation
- File size limits
- Content type validation
- SQL injection prevention via ORM
- XSS prevention via Pydantic

## Performance Optimization

### Caching Strategy
- Redis for session data (future)
- In-memory caching for hot data
- HTTP caching headers

### Async Processing
- Background tasks for heavy operations
- Celery for distributed tasks (future)
- Event-driven architecture

### Response Optimization
- Pagination for list endpoints
- Field filtering via query params
- Compression for large responses

## Testing Approach

### Unit Tests
```python
async def test_upload_audio():
    async with AsyncClient(app=app) as client:
        response = await client.post(
            "/api/meeting/upload",
            files={"file": ("test.wav", audio_bytes, "audio/wav")},
            data={"meeting_id": "test-123"}
        )
        assert response.status_code == 200
```

### Integration Tests
- Mock external services
- Test database transactions
- Validate error scenarios

## Development Patterns

### Adding New Endpoints
1. Define Pydantic models
2. Create router function
3. Inject dependencies
4. Delegate to service
5. Add tests
6. Update OpenAPI docs

### Debugging SSE
```bash
# Test SSE endpoint
curl -N http://localhost:8000/api/meeting/123/stream

# Monitor with httpie
http --stream GET localhost:8000/api/meeting/123/stream
```

---

*This documentation covers the API layer patterns and implementation details. Update when adding new endpoints or changing patterns.*
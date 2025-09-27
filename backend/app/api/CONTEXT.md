# API Layer Context

## Router Overview
- `app/api/meeting.py` registers two routers:
  - `router` with prefix `/api/meeting` for current clients.
  - `legacy_router` exposing `/stream/{meeting_id}` for backward compatibility.
- Routes rely on dependency injection to retrieve `TranscriptService` instances
  and to resolve the raw audio directory.

## Endpoints
1. `POST /api/meeting/upload`
   - Accepts a single WAV file via `UploadFile`.
   - Validates MIME type against a strict allow list.
   - Streams the payload to disk in 1 MiB chunks to avoid loading the whole file
     into memory.
   - Returns a JSON body containing the generated `meeting_id`.

2. `GET /api/meeting/{meeting_id}/stream`
   - Ensures the audio file exists before starting the response.
   - Wraps the service's async generator into a `StreamingResponse` with
     `text/event-stream` content type.
   - Emits `event: transcript` entries followed by a final `event: summary`.

3. `GET /stream/{meeting_id}`
   - Same behaviour as the prefixed SSE endpoint but kept out of OpenAPI for
     legacy integrations.

## Supporting Utilities
- `_transcript_service_dependency` allows overriding the gRPC client type via a
  query parameter so tests can force real/mock behaviour.
- `_iter_upload_file` yields file chunks asynchronously to support very large
  uploads without blocking the event loop.
- `_serialize_stream_item` converts `TranscriptService` payloads to SSE-compliant
  strings (with UTF-8 safe JSON encoding).

## Interaction With Other Layers
- `TranscriptService` handles raw audio resolution, meeting processing, and event
  generation.
- Repositories accessed by downstream services rely on `AsyncSession` instances
  provided through dependency overrides in tests.
- Loguru middleware in `app.main` captures request metadata for all endpoints in
  this router.

## Testing Strategy
- `backend/tests/test_api_meeting.py` covers happy paths and error scenarios for
  uploads and SSE streaming.
- Fixtures from `backend/tests/conftest.py` supply temporary storage directories
  and database sessions.
- SSE tests consume the async generator directly to avoid flaky network timing.

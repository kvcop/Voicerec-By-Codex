# Backend - Component Context

## Purpose
The FastAPI backend exposes upload and streaming APIs for meeting transcripts,
coordinates ML processing through mocked gRPC clients, and persists meeting
metadata via SQLAlchemy repositories.

## Current Status
- Audio upload and SSE streaming endpoints are implemented under
  `/api/meeting`.
- Structured Loguru logging with HTTP middleware is enabled during app
  initialization.
- SQLAlchemy models (`User`, `Meeting`, `Transcript`) and repositories provide
  CRUD access to the database.
- Test infrastructure provisions an async SQLite database per test with
  dependency overrides for FastAPI routes.

## Key Modules
- `app/main.py` – application factory, logging middleware, router wiring.
- `app/api/meeting.py` – upload & SSE routes plus legacy streaming path.
- `app/services/transcript.py` – orchestrates audio storage and meeting
  processing pipeline.
- `app/core/logging.py` – Loguru configuration.
- `app/core/settings.py` – Pydantic settings including `RAW_AUDIO_DIR`.
- `app/db/base.py` – declarative base and metadata naming conventions.
- `app/db/repositories/` – repository implementations for each model.
- `app/db/session.py` – cached async engine and session factory helpers.
- `app/db/schema.py` – validates the database migration version during startup.
- `backend/tests/conftest.py` – async SQLite fixtures and FastAPI overrides.

## Request Flow Overview
1. `POST /api/meeting/upload` streams validated WAV files to
   `RAW_AUDIO_DIR` (default `data/raw/`) chunk by chunk.
2. The endpoint returns a `meeting_id` that maps to the stored audio file.
3. `GET /api/meeting/{meeting_id}/stream` resolves the audio path and starts
   SSE streaming via `TranscriptService`.
4. `TranscriptService` delegates to `MeetingProcessingService`, which fans
   out to mocked gRPC clients (transcribe/diarize/summarize fixtures) and
   yields transcript events plus a final summary.
5. Repositories write transcript metadata to the database when applicable
   (current mocks keep data in memory; persistence hooks are ready).

## Logging & Observability
- `configure_logging()` installs a JSON sink with log level taken from the
  `LOG_LEVEL` environment variable.
- HTTP middleware binds method, path, query, status code, and elapsed time to
  each request log entry. Failures emit structured stack traces.

## Test Infrastructure
- `db_engine` fixture provisions a fresh SQLite database using `aiosqlite` and
  creates the schema via `Base.metadata.create_all`.
- `db_session` and `fastapi_db_session` fixtures share transactional sessions
  that roll back after each test.
- FastAPI dependency overrides inject the temporary session into runtime code,
  allowing API tests to execute against the transient database.
- gRPC interactions rely on JSON fixtures stored in `backend/tests/fixtures/`.

## Next Steps
- Integrate real persistence for transcript artifacts once the ML pipeline
  moves beyond mocks.
- Expand repository usage inside services to persist streamed events.
- Add authentication and authorization once product requirements are defined.

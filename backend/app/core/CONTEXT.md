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

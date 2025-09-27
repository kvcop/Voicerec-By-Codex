"""Main application entry point."""

from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from loguru import logger

from app.api.meeting import router as meeting_router
from app.core.logging import configure_logging

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.responses import Response

configure_logging()

app = FastAPI(title='Meeting Recognizer')


@app.middleware('http')
async def http_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Log inbound HTTP requests with structured Loguru output."""
    start_time = perf_counter()
    request_logger = logger.bind(
        http_method=request.method,
        http_path=request.url.path,
        http_query=request.url.query or None,
    )
    request_logger.info('request.started')

    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (perf_counter() - start_time) * 1000
        request_logger.bind(elapsed_ms=round(elapsed_ms, 2)).exception('request.failed')
        raise

    elapsed_ms = (perf_counter() - start_time) * 1000
    request_logger.bind(
        status_code=response.status_code,
        elapsed_ms=round(elapsed_ms, 2),
    ).info('request.completed')
    return response


app.include_router(meeting_router)


@app.get('/health')
def health_check() -> dict[str, str]:
    """Return service health status."""
    return {'status': 'ok'}

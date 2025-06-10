"""Main application entry point."""

from fastapi import FastAPI

from app.api.meeting import router as meeting_router

app = FastAPI(title='Meeting Recognizer')

app.include_router(meeting_router)


@app.get('/health')
def health_check() -> dict[str, str]:
    """Return service health status."""
    return {'status': 'ok'}

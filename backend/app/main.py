"""Main application entry point."""

from fastapi import FastAPI

app = FastAPI(title='Meeting Recognizer')


@app.get('/health')
def health_check() -> dict[str, str]:
    """Return service health status."""
    return {'status': 'ok'}

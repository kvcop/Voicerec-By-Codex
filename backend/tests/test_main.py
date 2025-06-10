"""Tests for main application routes."""

from http import HTTPStatus

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Health endpoint returns OK status."""
    response = client.get('/health')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'status': 'ok'}

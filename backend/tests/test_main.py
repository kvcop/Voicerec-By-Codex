"""Tests for main application routes."""

import logging
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from loguru import logger

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Health endpoint returns OK status."""
    response = client.get('/health')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'status': 'ok'}


def test_http_logging_middleware_logs_completed_request(caplog: pytest.LogCaptureFixture) -> None:
    """HTTP middleware emits structured log for completed requests."""
    caplog.set_level(logging.INFO)
    token = logger.add(caplog.handler, level='INFO', format='{message}')
    try:
        response = client.get('/health')
    finally:
        logger.remove(token)

    assert response.status_code == HTTPStatus.OK
    messages = [record.message for record in caplog.records]
    assert any('request.completed' in message for message in messages)

"""Asynchronous mock gRPC clients."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from pathlib import Path


class MockTranscribeClient:
    """Return transcript fixture instead of real gRPC call."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path
        self._cached_data: dict[str, Any] | None = None

    async def run(self, _: Path) -> dict[str, Any]:
        """Return transcript data from fixture."""
        if self._cached_data is None:
            self._cached_data = json.loads(self._fixture_path.read_text(encoding='utf-8'))
        return self._cached_data  # type: ignore[return-value]


class MockDiarizeClient:
    """Return diarization fixture instead of real gRPC call."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path
        self._cached_data: dict[str, Any] | None = None

    async def run(self, _: Path) -> dict[str, Any]:
        """Return diarization data from fixture."""
        if self._cached_data is None:
            self._cached_data = json.loads(self._fixture_path.read_text(encoding='utf-8'))
        return self._cached_data  # type: ignore[return-value]


class MockSummarizeClient:
    """Return summary fixture instead of real gRPC call."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path
        self._cached_data: dict[str, Any] | None = None

    async def run(self, _: str) -> dict[str, Any]:
        """Return summary data from fixture."""
        if self._cached_data is None:
            self._cached_data = json.loads(self._fixture_path.read_text(encoding='utf-8'))
        return self._cached_data  # type: ignore[return-value]


Client = MockTranscribeClient | MockDiarizeClient | MockSummarizeClient


def create_grpc_client(
    service: str,
    fixture_path: Path,
    client_type: str | None = None,
) -> Client:
    """Return a mock gRPC client instance.

    Args:
        service: Name of the service to use. Supported values are
            ``transcribe``, ``diarize`` and ``summarize``.
        fixture_path: Path to the response fixture.
        client_type: Optional client implementation type. If ``None`` the
            ``GRPC_CLIENT_TYPE`` environment variable is used. Only ``mock`` is
            supported at the moment.

    Returns:
        Instantiated gRPC client ready for calls.

    Raises:
        ValueError: If ``client_type`` or ``service`` is invalid.
    """
    client_type = client_type or os.getenv('GRPC_CLIENT_TYPE', 'mock')
    if client_type != 'mock':
        message = f'Unsupported client type: {client_type}'
        raise ValueError(message)

    mapping: dict[str, type[Client]] = {
        'transcribe': MockTranscribeClient,
        'diarize': MockDiarizeClient,
        'summarize': MockSummarizeClient,
    }

    try:
        client_cls = mapping[service]
    except KeyError as exc:
        message = f'Unknown service: {service}'
        raise ValueError(message) from exc

    return client_cls(fixture_path)

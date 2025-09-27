"""Asynchronous gRPC clients and factory utilities."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import grpc  # type: ignore[import-untyped]

from app.clients import DiarizeGrpcClient, SummarizeGrpcClient, TranscribeGrpcClient
from app.core.settings import GPUSettings  # noqa: TC001

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from collections.abc import AsyncIterator, Iterable

    from grpc import aio as grpc_aio


class MockTranscribeClient:
    """Return transcript fixture instead of real gRPC call."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path
        self._cached_data: dict[str, Any] | None = None

    async def run(self, source: Iterable[bytes]) -> dict[str, Any]:
        """Return transcript data from fixture."""
        _consume_stream(source)
        if self._cached_data is None:
            self._cached_data = json.loads(self._fixture_path.read_text(encoding='utf-8'))
        return copy.deepcopy(self._cached_data)

    async def stream_run(self, _: Path) -> AsyncIterator[dict[str, Any]]:
        """Yield transcript fragments read from fixture."""
        payload = await self.run([b''])
        segments = payload.get('segments')
        if isinstance(segments, list):
            for segment in segments:
                if isinstance(segment, dict):
                    yield {'segment': copy.deepcopy(segment)}
            return

        text = payload.get('text')
        if isinstance(text, str):
            yield {'text': text}


class MockDiarizeClient:
    """Return diarization fixture instead of real gRPC call."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path
        self._cached_data: dict[str, Any] | None = None

    async def run(self, source: Iterable[bytes]) -> dict[str, Any]:
        """Return diarization data from fixture."""
        _consume_stream(source)
        if self._cached_data is None:
            self._cached_data = json.loads(self._fixture_path.read_text(encoding='utf-8'))
        return copy.deepcopy(self._cached_data)

    async def stream_run(self, _: Path) -> AsyncIterator[dict[str, Any]]:
        """Yield diarization segments from fixture."""
        payload = await self.run([b''])
        segments = payload.get('segments')
        if isinstance(segments, list):
            for segment in segments:
                if isinstance(segment, dict):
                    yield copy.deepcopy(segment)


class MockSummarizeClient:
    """Return summary fixture instead of real gRPC call."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path
        self._cached_data: dict[str, Any] | None = None

    async def run(self, _: str) -> dict[str, Any]:
        """Return summary data from fixture."""
        if self._cached_data is None:
            self._cached_data = json.loads(self._fixture_path.read_text(encoding='utf-8'))
        return copy.deepcopy(self._cached_data)

    async def stream_run(self, _: str) -> AsyncIterator[dict[str, Any]]:
        """Yield summary payload from fixture."""
        yield await self.run('')


RealTranscribeClient = TranscribeGrpcClient
RealDiarizeClient = DiarizeGrpcClient
RealSummarizeClient = SummarizeGrpcClient

Client = (
    MockTranscribeClient
    | MockDiarizeClient
    | MockSummarizeClient
    | RealTranscribeClient
    | RealDiarizeClient
    | RealSummarizeClient
)


def _load_certificate(path: str | None) -> bytes | None:
    """Read certificate contents if path is provided."""
    if not path:
        return None
    return Path(path).expanduser().read_bytes()


def _create_channel(settings: GPUSettings) -> grpc_aio.Channel:
    """Create gRPC channel based on GPU settings."""
    target = f'{settings.grpc_host}:{settings.grpc_port}'
    if settings.grpc_use_tls:
        credentials = grpc.ssl_channel_credentials(
            root_certificates=_load_certificate(settings.grpc_tls_ca),
            private_key=_load_certificate(settings.grpc_tls_key),
            certificate_chain=_load_certificate(settings.grpc_tls_cert),
        )
        return grpc.aio.secure_channel(target, credentials)
    return grpc.aio.insecure_channel(target)


def _consume_stream(stream: Iterable[bytes]) -> None:
    """Read the entire stream to emulate GPU client behaviour."""
    for chunk in stream:
        if not isinstance(chunk, (bytes, bytearray)):
            message = 'Audio chunks must be bytes-like'
            raise TypeError(message)


def create_grpc_client(
    service: str,
    fixture_path: Path | None = None,
    client_type: str | None = None,
    *,
    gpu_settings: GPUSettings | None = None,
) -> Client:
    """Return a mock gRPC client instance.

    Args:
        service: Name of the service to use. Supported values are
            ``transcribe``, ``diarize`` and ``summarize``.
        fixture_path: Path to the response fixture, required for ``mock`` clients.
        client_type: Optional client implementation type. If ``None`` the
            ``GRPC_CLIENT_TYPE`` environment variable is used.
        gpu_settings: GPU settings used for the real gRPC client implementation.

    Returns:
        Instantiated gRPC client ready for calls.

    Raises:
        ValueError: If ``client_type`` or ``service`` is invalid.
    """
    client_type = client_type or os.getenv('GRPC_CLIENT_TYPE', 'mock')

    mapping_mock: dict[str, type[Any]] = {
        'transcribe': MockTranscribeClient,
        'diarize': MockDiarizeClient,
        'summarize': MockSummarizeClient,
    }

    mapping_real: dict[str, type[Any]] = {
        'transcribe': RealTranscribeClient,
        'diarize': RealDiarizeClient,
        'summarize': RealSummarizeClient,
    }

    if client_type == 'mock':
        if fixture_path is None:
            message = 'fixture_path is required for mock clients'
            raise ValueError(message)
        try:
            client_cls = mapping_mock[service]
        except KeyError as exc:
            message = f'Unknown service: {service}'
            raise ValueError(message) from exc
        return client_cls(fixture_path)

    if client_type == 'grpc':
        if gpu_settings is None:
            message = 'gpu_settings is required for grpc clients'
            raise ValueError(message)
        try:
            client_cls = mapping_real[service]
        except KeyError as exc:
            message = f'Unknown service: {service}'
            raise ValueError(message) from exc
        channel = _create_channel(gpu_settings)
        return client_cls(channel)

    message = f'Unsupported client type: {client_type}'
    raise ValueError(message)

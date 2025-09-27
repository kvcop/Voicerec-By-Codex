"""Integration-style tests for gRPC client configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NoReturn

import pytest

from app.core.settings import GPUSettings
from app.grpc_client import RealTranscribeClient, create_grpc_client

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from pathlib import Path


class _FakeUnaryUnary:
    def __call__(self, *_: object) -> None:
        raise RuntimeError


class _FakeChannel:
    """Minimal channel stub emulating grpc.aio.Channel behavior."""

    def __init__(self, target: str) -> None:
        self.target = target
        self.recorded_methods: list[str] = []

    def unary_unary(self, method: str, *_: object) -> _FakeUnaryUnary:
        self.recorded_methods.append(method)
        return _FakeUnaryUnary()

    async def close(self) -> None:
        return None


class _DummyStub:
    """Lightweight stub with the expected interface."""

    async def Run(self, *_: object) -> None:  # noqa: N802
        raise RuntimeError


@pytest.mark.asyncio
async def test_insecure_channel_used_for_non_tls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Factory builds insecure channel when TLS is disabled."""
    created_targets: list[str] = []

    def fake_insecure_channel(target: str) -> _FakeChannel:
        created_targets.append(target)
        return _FakeChannel(target)

    monkeypatch.setattr('app.grpc_client.grpc.aio.insecure_channel', fake_insecure_channel)

    def fail_secure_channel(*_: object) -> NoReturn:
        pytest.fail('secure channel should not be used')

    monkeypatch.setattr('app.grpc_client.grpc.aio.secure_channel', fail_secure_channel)

    def build_transcribe_stub(_: object) -> _DummyStub:
        return _DummyStub()

    monkeypatch.setattr(
        'app.clients.grpc_clients.transcribe_pb2_grpc.TranscribeStub',
        build_transcribe_stub,
    )

    settings = GPUSettings(grpc_host='localhost', grpc_port=50051, grpc_use_tls=False)
    client = create_grpc_client('transcribe', client_type='grpc', gpu_settings=settings)

    assert isinstance(client, RealTranscribeClient)
    assert created_targets == ['localhost:50051']


@pytest.mark.asyncio
async def test_secure_channel_uses_tls_credentials(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """TLS configuration creates secure channel with provided certificates."""
    ca = tmp_path / 'ca.pem'
    key = tmp_path / 'client.key'
    cert = tmp_path / 'client.pem'
    ca.write_text('ca-cert', encoding='utf-8')
    key.write_text('client-key', encoding='utf-8')
    cert.write_text('client-cert', encoding='utf-8')

    recorded: dict[str, Any] = {}

    def fake_credentials(
        *,
        root_certificates: bytes | None,
        private_key: bytes | None,
        certificate_chain: bytes | None,
    ) -> object:
        recorded['root'] = root_certificates
        recorded['key'] = private_key
        recorded['chain'] = certificate_chain
        return object()

    def fake_secure_channel(target: str, credentials: object) -> _FakeChannel:
        recorded['target'] = target
        recorded['credentials'] = credentials
        return _FakeChannel(target)

    def wrap_credentials(**kwargs: object) -> object:
        return fake_credentials(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr('app.grpc_client.grpc.ssl_channel_credentials', wrap_credentials)
    monkeypatch.setattr('app.grpc_client.grpc.aio.secure_channel', fake_secure_channel)

    def fail_insecure_channel(*_: object) -> NoReturn:
        pytest.fail('insecure channel should not be used')

    monkeypatch.setattr('app.grpc_client.grpc.aio.insecure_channel', fail_insecure_channel)

    def build_summarize_stub(_: object) -> _DummyStub:
        return _DummyStub()

    monkeypatch.setattr(
        'app.clients.grpc_clients.summarize_pb2_grpc.SummarizeStub',
        build_summarize_stub,
    )

    settings = GPUSettings(
        grpc_host='gpu.example.com',
        grpc_port=443,
        grpc_use_tls=True,
        grpc_tls_ca=str(ca),
        grpc_tls_key=str(key),
        grpc_tls_cert=str(cert),
    )

    create_grpc_client('summarize', client_type='grpc', gpu_settings=settings)

    assert recorded['target'] == 'gpu.example.com:443'
    assert recorded['root'] == ca.read_bytes()
    assert recorded['key'] == key.read_bytes()
    assert recorded['chain'] == cert.read_bytes()

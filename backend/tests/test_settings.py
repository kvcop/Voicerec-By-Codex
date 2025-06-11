"""Tests for GPUSettings validators."""

from __future__ import annotations

import importlib

import pytest
from pydantic import ValidationError

MODULE_PATH = 'app.core.settings'


def _load_gpu_settings() -> type:
    module = importlib.import_module(MODULE_PATH)
    importlib.reload(module)
    return module.GPUSettings


def test_tls_requires_certificates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validator raises error when TLS enabled without certificates."""
    monkeypatch.setenv('GPU_GRPC_HOST', 'h')
    monkeypatch.setenv('GPU_GRPC_PORT', '1')
    gpu_settings = _load_gpu_settings()
    with pytest.raises(ValidationError):
        gpu_settings(grpc_host='h', grpc_port=1, grpc_use_tls=True)


def test_tls_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    """GPUSettings is created when all certificates provided."""
    monkeypatch.setenv('GPU_GRPC_HOST', 'h')
    monkeypatch.setenv('GPU_GRPC_PORT', '1')
    gpu_settings = _load_gpu_settings()
    settings = gpu_settings(
        grpc_host='h',
        grpc_port=1,
        grpc_use_tls=True,
        grpc_tls_ca='ca',
        grpc_tls_cert='cert',
        grpc_tls_key='key',
    )
    assert settings.grpc_tls_cert == 'cert'

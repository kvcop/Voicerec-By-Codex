"""Tests for GPUSettings validators and settings module behavior."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

MODULE_PATH = 'app.core.settings'

if TYPE_CHECKING:
    from types import ModuleType


def _reload_settings_module() -> ModuleType:
    module = importlib.import_module(MODULE_PATH)
    return importlib.reload(module)


def _load_gpu_settings() -> type:
    module = _reload_settings_module()
    return module.GPUSettings


def test_settings_module_import_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings module can be imported without environment variables set."""
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('GPU_GRPC_HOST', raising=False)
    monkeypatch.delenv('GPU_GRPC_PORT', raising=False)

    module = _reload_settings_module()

    assert hasattr(module, 'Settings')


def test_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Creating Settings without the required DATABASE_URL fails validation."""
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('GPU_GRPC_HOST', raising=False)
    monkeypatch.delenv('GPU_GRPC_PORT', raising=False)

    module = _reload_settings_module()

    with pytest.raises(ValidationError):
        module.Settings()


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings returns the same instance on repeated calls."""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://example')
    monkeypatch.setenv('GPU_GRPC_HOST', 'host')
    monkeypatch.setenv('GPU_GRPC_PORT', '1234')

    module = _reload_settings_module()

    first = module.get_settings()
    second = module.get_settings()

    assert first is second


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

"""Tests for the GPU summarization gRPC service."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

summarize_service = importlib.import_module('gpu_services.summarize_service')
summarize_pb2_module = importlib.import_module('app.clients.summarize_pb2')

summarize_pb2 = cast('Any', summarize_pb2_module)


class _AbortCalledError(RuntimeError):
    """Signal that the gRPC context requested to abort the request."""


@dataclass(slots=True)
class _DummyContext:
    """Collect abort requests issued by the service under test."""

    abort_calls: list[tuple[object, str]]

    def abort(self, code: object, details: str) -> None:
        """Record the abort request and raise an exception to stop execution."""
        self.abort_calls.append((code, details))
        raise _AbortCalledError(code, details)


class _SummaryRequestFactory(Protocol):
    """Protocol describing the TextRequest constructor used in the tests."""

    def __call__(self, *, text: str) -> object:
        """Return a new TextRequest message."""


class _SummaryMessageLike(Protocol):
    """Protocol describing the Summary response used by the tests."""

    text: str


class _SummarizeServiceLike(Protocol):
    """Protocol describing the subset of the summarization service used in tests."""

    def run(self, request: object, context: object) -> object:
        """Execute the summarization request."""


def _build_service(monkeypatch: pytest.MonkeyPatch) -> _SummarizeServiceLike:
    """Instantiate the summarization service with minimal configuration."""
    monkeypatch.setenv('LLM_API_BASE', 'https://llm.invalid')
    monkeypatch.setenv('LLM_API_KEY', 'test-key')
    return summarize_service.SummarizeService()


def test_run_returns_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    """`SummarizeService.run` should return the generated summary text."""
    service = _build_service(monkeypatch)
    text_request_cls = summarize_pb2.TextRequest
    request_factory = cast('_SummaryRequestFactory', text_request_cls)
    request = request_factory(text='Decide on deployment steps and owners.')
    context = _DummyContext([])

    captured: dict[str, object] = {}

    def _fake_generate_summary(
        self: _SummarizeServiceLike,
        text: str,
        ctx: object,
    ) -> str:
        del self
        captured['text'] = text
        captured['context'] = ctx
        return 'Deployment summary with assigned owners.'

    monkeypatch.setattr(
        summarize_service.SummarizeService,
        '_generate_summary',
        _fake_generate_summary,
    )

    response = cast('_SummaryMessageLike', service.run(request, context))

    assert response.text == 'Deployment summary with assigned owners.'
    assert captured['text'] == 'Decide on deployment steps and owners.'
    assert captured['context'] is context
    assert context.abort_calls == []


def test_run_aborts_on_empty_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """The service should abort gRPC requests that lack source text."""
    service = _build_service(monkeypatch)
    text_request_cls = summarize_pb2.TextRequest
    request_factory = cast('_SummaryRequestFactory', text_request_cls)
    request = request_factory(text='   ')
    context = _DummyContext([])

    with pytest.raises(_AbortCalledError) as exc_info:
        service.run(request, context)

    assert exc_info.value.args[0] == summarize_service.grpc.StatusCode.INVALID_ARGUMENT
    expected_error = 'Source text must be provided for summarization'
    assert context.abort_calls == [
        (summarize_service.grpc.StatusCode.INVALID_ARGUMENT, expected_error)
    ]

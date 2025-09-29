"""Summarization gRPC service bootstrap."""

from __future__ import annotations

import importlib
import logging
import os
from concurrent import futures
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

import httpx

from app.clients import summarize_pb2, summarize_pb2_grpc

if TYPE_CHECKING:

    class TextRequest(Protocol):
        """Typed representation of the summarize.TextRequest message."""

        text: str

    class Summary(Protocol):
        """Typed representation of the summarize.Summary message."""

        text: str

    class SummarizeServicer(Protocol):
        """Protocol for the generated Summarize service base class."""

    def add_summarize_servicer_to_server(servicer: SummarizeServicer, server: object) -> None:
        """Register the summarization servicer with the gRPC server."""

else:  # pragma: no cover - runtime fallbacks
    TextRequest = summarize_pb2.TextRequest
    Summary = summarize_pb2.Summary
    SummarizeServicer = summarize_pb2_grpc.SummarizeServicer
    add_summarize_servicer_to_server = summarize_pb2_grpc.add_SummarizeServicer_to_server

grpc = importlib.import_module('grpc')


class ServicerContext(Protocol):
    """Minimal subset of the gRPC servicer context used by the summarizer."""

    def abort(self, code: object, details: str) -> None:
        """Abort the gRPC request with the provided error details."""


class GrpcServer(Protocol):
    """Subset of the gRPC server API required by the summarization bootstrap."""

    def add_insecure_port(self, address: str) -> None:  # pragma: no cover - gRPC runtime
        """Expose the server on the provided address."""

    def start(self) -> None:  # pragma: no cover - gRPC runtime
        """Start processing incoming requests."""

    def wait_for_termination(self) -> None:  # pragma: no cover - gRPC runtime
        """Block until the server shuts down."""


LOGGER = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    'You are an assistant that condenses meeting transcripts '
    'into concise action-oriented summaries.'
)
DEFAULT_MODEL_NAME = 'qwen-3'
DEFAULT_TEMPERATURE = 0.25
DEFAULT_TIMEOUT_SECONDS = 60.0
HTTP_SERVER_ERROR_MIN = 500
HTTP_SERVER_ERROR_MAX = 600


@dataclass(frozen=True)
class SummarizerSettings:
    """Configuration container for calling the external LLM API."""

    api_base: str
    api_key: str
    model: str
    temperature: float
    timeout_seconds: float
    system_prompt: str

    @classmethod
    def from_env(cls) -> SummarizerSettings:
        """Load summarizer configuration from environment variables."""
        api_base = os.getenv('LLM_API_BASE', '').strip()
        if not api_base:
            message = 'LLM_API_BASE must be configured for the summarization service'
            raise RuntimeError(message)

        api_key = os.getenv('LLM_API_KEY', '').strip()
        if not api_key:
            message = 'LLM_API_KEY must be configured for the summarization service'
            raise RuntimeError(message)

        model = os.getenv('LLM_MODEL', DEFAULT_MODEL_NAME).strip() or DEFAULT_MODEL_NAME

        temperature_value = os.getenv('LLM_TEMPERATURE', str(DEFAULT_TEMPERATURE)).strip()
        try:
            temperature = float(temperature_value)
        except ValueError as exc:  # pragma: no cover - defensive guard
            message = 'LLM_TEMPERATURE must be a valid float value'
            raise RuntimeError(message) from exc

        timeout_value = os.getenv(
            'LLM_REQUEST_TIMEOUT_SECONDS',
            str(DEFAULT_TIMEOUT_SECONDS),
        ).strip()
        try:
            timeout_seconds = float(timeout_value)
        except ValueError as exc:  # pragma: no cover - defensive guard
            message = 'LLM_REQUEST_TIMEOUT_SECONDS must be a valid float value'
            raise RuntimeError(message) from exc

        system_prompt = os.getenv('LLM_SYSTEM_PROMPT', DEFAULT_SYSTEM_PROMPT).strip()
        if not system_prompt:
            system_prompt = DEFAULT_SYSTEM_PROMPT

        return cls(
            api_base=api_base,
            api_key=api_key,
            model=model,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            system_prompt=system_prompt,
        )


class SummarizeService(SummarizeServicer):
    """gRPC servicer for the meeting summarization pipeline."""

    def __init__(self) -> None:
        """Initialise the HTTP client and summarizer configuration."""
        self._settings = SummarizerSettings.from_env()
        LOGGER.info('Summarization service configured to use model %s', self._settings.model)
        self._client = httpx.Client(
            base_url=self._settings.api_base,
            headers={
                'Authorization': f'Bearer {self._settings.api_key}',
                'Content-Type': 'application/json',
            },
            timeout=self._settings.timeout_seconds,
        )

    def run(self, request: TextRequest, context: ServicerContext) -> Summary:
        """Handle summarization requests.

        Args:
            request: Incoming gRPC request with source text.
            context: gRPC request context.

        Returns:
            Generated summary text produced by the external LLM.
        """
        source_text = (request.text or '').strip()
        if not source_text:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                'Source text must be provided for summarization',
            )

        LOGGER.info('Received summarization request (length=%d)', len(source_text))

        try:
            summary_text = self._generate_summary(source_text, context)
        except grpc.RpcError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception('Unexpected error during summarization request handling')
            context.abort(grpc.StatusCode.INTERNAL, f'Unexpected summarization failure: {exc}')

        summary_cls = getattr(summarize_pb2, 'Summary')  # noqa: B009
        response = summary_cls(text=summary_text)
        return cast('Summary', response)

    Run = run

    def _generate_summary(self, text: str, context: ServicerContext) -> str:
        """Invoke the configured LLM API and return the resulting summary."""
        payload = {
            'model': self._settings.model,
            'temperature': self._settings.temperature,
            'messages': [
                {'role': 'system', 'content': self._settings.system_prompt},
                {'role': 'user', 'content': text},
            ],
        }

        try:
            response = self._client.post('chat/completions', json=payload)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            LOGGER.error('LLM API request timed out: %s', exc)
            context.abort(grpc.StatusCode.DEADLINE_EXCEEDED, 'LLM API request timed out')
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            LOGGER.error('LLM API returned HTTP %s: %s', status_code, exc.response.text)
            if HTTP_SERVER_ERROR_MIN <= status_code < HTTP_SERVER_ERROR_MAX:
                context.abort(grpc.StatusCode.UNAVAILABLE, 'LLM API is temporarily unavailable')
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, 'LLM API rejected the request')
        except httpx.RequestError:
            LOGGER.exception('Failed to reach LLM API endpoint')
            context.abort(grpc.StatusCode.UNAVAILABLE, 'Failed to reach LLM API endpoint')

        try:
            payload_data = response.json()
        except ValueError as exc:
            LOGGER.error('Failed to decode LLM API response as JSON: %s', exc)
            context.abort(grpc.StatusCode.INTERNAL, 'Failed to decode LLM API response')

        try:
            summary_text = self._extract_summary(payload_data)
        except ValueError as exc:
            LOGGER.error('Unexpected response schema from LLM API: %s', payload_data)
            context.abort(grpc.StatusCode.INTERNAL, str(exc))

        if not summary_text:
            context.abort(grpc.StatusCode.INTERNAL, 'LLM API returned an empty summary')

        LOGGER.debug('Generated summary length=%d', len(summary_text))
        return summary_text

    @staticmethod
    def _extract_summary(payload: dict[str, Any]) -> str:
        """Extract the textual summary content from the LLM response."""
        try:
            choices = payload['choices']
            first_choice = choices[0]
            message = first_choice['message']
            content = message['content']
        except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
            error_message = 'LLM API response did not include summary content'
            raise ValueError(error_message) from exc

        if not isinstance(content, str):  # pragma: no cover - defensive
            error_message = 'LLM API response content must be a string'
            raise TypeError(error_message)

        return content.strip()


def _create_server(max_workers: int) -> GrpcServer:
    """Instantiate a gRPC server for the summarization service."""
    return grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))


def serve() -> None:
    """Start the summarization gRPC service."""
    logging.basicConfig(level=os.getenv('SUMMARIZE_LOG_LEVEL', 'INFO'))
    port = os.getenv('SUMMARIZE_SERVICE_PORT', '50053')
    max_workers = int(os.getenv('SUMMARIZE_MAX_WORKERS', '4'))

    server = _create_server(max_workers=max_workers)
    add_summarize_servicer_to_server(SummarizeService(), server)
    server.add_insecure_port(f'[::]:{port}')

    LOGGER.info('Starting summarization service on port %s', port)
    server.start()
    server.wait_for_termination()


def main() -> None:
    """Entrypoint for running the summarization service as a module."""
    serve()


if __name__ == '__main__':
    main()

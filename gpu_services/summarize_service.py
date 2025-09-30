"""Summarization gRPC service bootstrap."""

from __future__ import annotations

import importlib
import json
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
DEFAULT_CHUNK_SIZE = 4000
DEFAULT_CHUNK_OVERLAP = 300
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
    chunk_size: int
    chunk_overlap: int

    @classmethod
    def from_env(cls) -> SummarizerSettings:
        """Load summarizer configuration from environment variables."""
        api_base_raw = cls._get_required_env('LLM_API_BASE')
        api_base = cls._normalize_api_base(api_base_raw)

        api_key = cls._get_required_env('LLM_API_KEY')
        model = os.getenv('LLM_MODEL', DEFAULT_MODEL_NAME).strip() or DEFAULT_MODEL_NAME
        temperature = cls._get_float_env('LLM_TEMPERATURE', DEFAULT_TEMPERATURE)
        timeout_seconds = cls._get_float_env('LLM_REQUEST_TIMEOUT_SECONDS', DEFAULT_TIMEOUT_SECONDS)

        system_prompt = os.getenv('LLM_SYSTEM_PROMPT', DEFAULT_SYSTEM_PROMPT).strip()
        if not system_prompt:
            system_prompt = DEFAULT_SYSTEM_PROMPT

        chunk_size = cls._get_int_env('LLM_CHUNK_SIZE', DEFAULT_CHUNK_SIZE, minimum=1)
        chunk_overlap = cls._get_int_env('LLM_CHUNK_OVERLAP', DEFAULT_CHUNK_OVERLAP, minimum=0)
        if chunk_overlap >= chunk_size:
            message = 'LLM_CHUNK_OVERLAP must be smaller than LLM_CHUNK_SIZE'
            raise RuntimeError(message)

        return cls(
            api_base=api_base,
            api_key=api_key,
            model=model,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            system_prompt=system_prompt,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    @staticmethod
    def _normalize_api_base(api_base: str) -> str:
        """Ensure the LLM API base URL retains trailing path segments."""
        if api_base.endswith('/'):
            return api_base
        return f'{api_base}/'

    @staticmethod
    def _get_required_env(name: str) -> str:
        """Return a required environment variable, ensuring it is not empty."""
        value = os.getenv(name, '').strip()
        if not value:
            message = f'{name} must be configured for the summarization service'
            raise RuntimeError(message)
        return value

    @staticmethod
    def _get_float_env(name: str, default: float) -> float:
        """Parse a float environment variable with fallback and validation."""
        raw_value = os.getenv(name, str(default)).strip()
        try:
            return float(raw_value)
        except ValueError as exc:  # pragma: no cover - defensive guard
            message = f'{name} must be a valid float value'
            raise RuntimeError(message) from exc

    @staticmethod
    def _get_int_env(name: str, default: int, *, minimum: int) -> int:
        """Parse an integer environment variable, enforcing a minimum bound."""
        raw_value = os.getenv(name, str(default)).strip()
        try:
            value = int(raw_value)
        except ValueError as exc:  # pragma: no cover - defensive guard
            message = f'{name} must be a valid integer'
            raise RuntimeError(message) from exc

        if value < minimum:
            comparator = 'than or equal to' if minimum == 0 else 'than'
            message = f'{name} must be greater {comparator} {minimum}'
            raise RuntimeError(message)

        return value


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
                'Content-Type': 'application/json; charset=utf-8',
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

        summary_text = self._generate_summary(source_text, context)

        summary_cls = getattr(summarize_pb2, 'Summary')  # noqa: B009
        response = summary_cls(text=summary_text)
        return cast('Summary', response)

    Run = run

    def _generate_summary(self, text: str, context: ServicerContext) -> str:
        """Invoke the configured LLM API and return the resulting summary."""
        chunks = self._split_into_chunks(text)
        if len(chunks) == 1:
            LOGGER.debug('Summarizing text in a single request (length=%d)', len(text))
            return self._request_summary(chunks[0], context)

        # Multi-stage summarization pipeline:
        # 1. Break the long transcript into overlapping chunks that fit the LLM context window.
        # 2. Summarize each chunk individually so that no information is lost.
        # 3. Combine the partial summaries and summarize them again to obtain the final result.
        LOGGER.info(
            'Summarizing text in %d chunks (chunk_size=%d, overlap=%d)',
            len(chunks),
            self._settings.chunk_size,
            self._settings.chunk_overlap,
        )

        partial_summaries: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            LOGGER.debug(
                'Generating partial summary %d/%d (length=%d)',
                index,
                len(chunks),
                len(chunk),
            )
            prompt = (
                'Summarize the following meeting segment, highlighting action items, '
                'decisions, and owner assignments.'
            )
            partial_summary = self._request_summary(f'{prompt}\n\n{chunk}', context)
            partial_summaries.append(partial_summary)

        combined_summary = '\n\n'.join(
            f'Segment {idx} summary:\n{summary}'
            for idx, summary in enumerate(partial_summaries, start=1)
        )

        final_prompt = (
            'Produce a cohesive meeting summary based on the provided segment summaries. '
            'Merge overlapping information, keep the timeline clear, and list actionable '
            'next steps.'
        )

        final_request = f'{final_prompt}\n\n{combined_summary}'
        return self._request_summary(final_request, context)

    def _request_summary(self, user_content: str, context: ServicerContext) -> str:
        """Call the remote LLM API with the provided user content."""
        payload = {
            'model': self._settings.model,
            'temperature': self._settings.temperature,
            'messages': [
                {'role': 'system', 'content': self._settings.system_prompt},
                {'role': 'user', 'content': user_content},
            ],
        }

        payload_data = self._execute_llm_request(payload, context)

        try:
            summary_text = self._extract_summary(payload_data)
        except ValueError as exc:
            LOGGER.error('Unexpected response schema from LLM API: %s', payload_data)
            context.abort(grpc.StatusCode.INTERNAL, str(exc))

        if not summary_text:
            context.abort(grpc.StatusCode.INTERNAL, 'LLM API returned an empty summary')

        LOGGER.debug('Generated summary length=%d', len(summary_text))
        return summary_text

    def _execute_llm_request(
        self,
        payload: dict[str, Any],
        context: ServicerContext,
    ) -> dict[str, Any]:
        """Send the payload to the LLM API and return the decoded JSON body."""
        payload_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')

        response: httpx.Response | None = None

        try:
            response = self._client.post('chat/completions', content=payload_bytes)
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
        except Exception:
            LOGGER.exception('Unexpected error while executing LLM API request')
            error_message = 'Unexpected error while executing LLM API request'
            context.abort(grpc.StatusCode.INTERNAL, error_message)

        try:
            if response is None:  # pragma: no cover - defensive guard
                error_message = 'LLM API response was not initialised'
                raise RuntimeError(error_message)

            if response.encoding is None:
                response.encoding = 'utf-8'
            payload_data = response.json()
        except ValueError as exc:
            LOGGER.error('Failed to decode LLM API response as JSON: %s', exc)
            context.abort(grpc.StatusCode.INTERNAL, 'Failed to decode LLM API response')

        return payload_data

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split the text into context-friendly chunks with optional overlap."""
        if len(text) <= self._settings.chunk_size:
            return [text]

        chunks: list[str] = []
        start = 0
        text_length = len(text)
        while start < text_length:
            end = min(text_length, start + self._settings.chunk_size)
            boundary = self._locate_chunk_boundary(text, start, end) if end < text_length else end

            boundary = max(boundary, start + 1)
            chunk = text[start:boundary].strip()
            if chunk:
                chunks.append(chunk)

            if boundary >= text_length:
                break

            overlap = min(self._settings.chunk_overlap, self._settings.chunk_size - 1)
            start = max(boundary - overlap, 0)

        return chunks

    def _locate_chunk_boundary(self, text: str, start: int, end: int) -> int:
        """Select a natural break point for a chunk, preferring paragraph or sentence ends."""
        paragraph_break = text.rfind('\n\n', start, end)
        if paragraph_break > start:
            return paragraph_break

        sentence_break = text.rfind('. ', start, end)
        if sentence_break > start:
            return sentence_break + 1

        word_break = text.rfind(' ', start, end)
        if word_break > start:
            return word_break

        return end

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

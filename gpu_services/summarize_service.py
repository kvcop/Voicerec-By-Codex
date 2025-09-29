"""Summarization gRPC service bootstrap."""

from __future__ import annotations

import importlib
import logging
import os
from concurrent import futures
from typing import TYPE_CHECKING, Protocol

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


class SummarizeService(SummarizeServicer):
    """gRPC servicer stub for the meeting summarization pipeline."""

    def run(self, request: TextRequest, context: ServicerContext) -> Summary:
        """Handle summarization requests.

        Args:
            request: Incoming gRPC request with source text.
            context: gRPC request context.

        Returns:
            Placeholder summary response until summarization is implemented.
        """
        text_length = len(request.text or '')
        LOGGER.info('Received summarization request (length=%d)', text_length)
        message = 'Summarization inference is not implemented yet.'
        context.abort(grpc.StatusCode.UNIMPLEMENTED, message)
        raise RuntimeError(message)

    Run = run


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

"""ASR gRPC service bootstrap."""

from __future__ import annotations

import importlib
import logging
import os
from concurrent import futures
from typing import TYPE_CHECKING, Protocol

from app.clients import transcribe_pb2, transcribe_pb2_grpc

if TYPE_CHECKING:

    class AudioRequest(Protocol):
        """Typed representation of the transcribe.AudioRequest message."""

        path: str

    class Transcript(Protocol):
        """Typed representation of the transcribe.Transcript message."""

        text: str

    class TranscribeServicer(Protocol):
        """Protocol for the generated Transcribe service base class."""

    def add_transcribe_servicer_to_server(servicer: TranscribeServicer, server: object) -> None:
        """Register the ASR servicer with the gRPC server."""

else:  # pragma: no cover - runtime fallbacks
    AudioRequest = transcribe_pb2.AudioRequest
    Transcript = transcribe_pb2.Transcript
    TranscribeServicer = transcribe_pb2_grpc.TranscribeServicer
    add_transcribe_servicer_to_server = transcribe_pb2_grpc.add_TranscribeServicer_to_server

grpc = importlib.import_module('grpc')


class ServicerContext(Protocol):
    """Minimal subset of the gRPC servicer context used by the ASR service."""

    def abort(self, code: object, details: str) -> None:
        """Abort the gRPC request with the provided error details."""


class GrpcServer(Protocol):
    """Subset of the gRPC server API required by the ASR bootstrap."""

    def add_insecure_port(self, address: str) -> None:  # pragma: no cover - gRPC runtime
        """Expose the server on the provided address."""

    def start(self) -> None:  # pragma: no cover - gRPC runtime
        """Start processing incoming requests."""

    def wait_for_termination(self) -> None:  # pragma: no cover - gRPC runtime
        """Block until the server shuts down."""


LOGGER = logging.getLogger(__name__)


class ASRService(TranscribeServicer):
    """gRPC servicer stub for the Whisper-based ASR pipeline."""

    def run(
        self,
        request: AudioRequest,
        context: ServicerContext,
    ) -> Transcript:
        """Handle transcription requests.

        Args:
            request: Incoming gRPC request with audio metadata.
            context: gRPC request context.

        Returns:
            Placeholder transcript response until ASR logic is implemented.
        """
        LOGGER.info('Received transcription request for path: %s', request.path or '<empty>')
        message = 'ASR inference is not implemented yet.'
        context.abort(grpc.StatusCode.UNIMPLEMENTED, message)
        raise RuntimeError(message)

    Run = run


def _create_server(max_workers: int) -> GrpcServer:
    """Instantiate a gRPC server for the ASR service."""
    return grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))


def serve() -> None:
    """Start the ASR gRPC service."""
    logging.basicConfig(level=os.getenv('ASR_LOG_LEVEL', 'INFO'))
    port = os.getenv('ASR_SERVICE_PORT', '50051')
    max_workers = int(os.getenv('ASR_MAX_WORKERS', '4'))

    server = _create_server(max_workers=max_workers)
    add_transcribe_servicer_to_server(ASRService(), server)
    server.add_insecure_port(f'[::]:{port}')

    LOGGER.info('Starting ASR service on port %s', port)
    server.start()
    server.wait_for_termination()


def main() -> None:
    """Entrypoint for running the ASR service as a module."""
    serve()


if __name__ == '__main__':
    main()

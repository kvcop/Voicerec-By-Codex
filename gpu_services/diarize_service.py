"""Speaker diarization gRPC service bootstrap."""

from __future__ import annotations

import importlib
import logging
import os
from concurrent import futures
from typing import TYPE_CHECKING, Protocol

from app.clients import diarize_pb2, diarize_pb2_grpc

if TYPE_CHECKING:

    class AudioRequest(Protocol):
        """Typed representation of the diarize.AudioRequest message."""

        path: str

    class Segment(Protocol):
        """Typed representation of the diarize.Segment message."""

        start: float
        end: float
        speaker: str

    class DiarizationResult(Protocol):
        """Typed representation of the diarize.DiarizationResult message."""

        segments: list[Segment]

    class DiarizeServicer(Protocol):
        """Protocol for the generated Diarize service base class."""

    def add_diarize_servicer_to_server(servicer: DiarizeServicer, server: object) -> None:
        """Register the diarization servicer with the gRPC server."""

else:  # pragma: no cover - runtime fallbacks
    AudioRequest = diarize_pb2.AudioRequest
    Segment = diarize_pb2.Segment
    DiarizationResult = diarize_pb2.DiarizationResult
    DiarizeServicer = diarize_pb2_grpc.DiarizeServicer
    add_diarize_servicer_to_server = diarize_pb2_grpc.add_DiarizeServicer_to_server

grpc = importlib.import_module('grpc')


class ServicerContext(Protocol):
    """Minimal subset of the gRPC servicer context used by the diarization service."""

    def abort(self, code: object, details: str) -> None:
        """Abort the gRPC request with the provided error details."""


class GrpcServer(Protocol):
    """Subset of the gRPC server API required by the diarization bootstrap."""

    def add_insecure_port(self, address: str) -> None:  # pragma: no cover - gRPC runtime
        """Expose the server on the provided address."""

    def start(self) -> None:  # pragma: no cover - gRPC runtime
        """Start processing incoming requests."""

    def wait_for_termination(self) -> None:  # pragma: no cover - gRPC runtime
        """Block until the server shuts down."""


LOGGER = logging.getLogger(__name__)


class DiarizeService(DiarizeServicer):
    """gRPC servicer stub for the NeMo-based speaker diarization pipeline."""

    def run(
        self,
        request: AudioRequest,
        context: ServicerContext,
    ) -> DiarizationResult:
        """Handle diarization requests.

        Args:
            request: Incoming gRPC request with audio metadata.
            context: gRPC request context.

        Returns:
            Placeholder diarization result until diarization logic is implemented.
        """
        LOGGER.info('Received diarization request for path: %s', request.path or '<empty>')
        message = 'Speaker diarization is not implemented yet.'
        context.abort(grpc.StatusCode.UNIMPLEMENTED, message)
        raise RuntimeError(message)

    Run = run


def _create_server(max_workers: int) -> GrpcServer:
    """Instantiate a gRPC server for the diarization service."""
    return grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))


def serve() -> None:
    """Start the diarization gRPC service."""
    logging.basicConfig(level=os.getenv('DIARIZATION_LOG_LEVEL', 'INFO'))
    port = os.getenv('DIARIZATION_SERVICE_PORT', '50052')
    max_workers = int(os.getenv('DIARIZATION_MAX_WORKERS', '4'))

    server = _create_server(max_workers=max_workers)
    add_diarize_servicer_to_server(DiarizeService(), server)
    server.add_insecure_port(f'[::]:{port}')

    LOGGER.info('Starting diarization service on port %s', port)
    server.start()
    server.wait_for_termination()


def main() -> None:
    """Entrypoint for running the diarization service as a module."""
    serve()


if __name__ == '__main__':
    main()

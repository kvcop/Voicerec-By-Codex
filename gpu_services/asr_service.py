"""ASR gRPC service bootstrap."""

from __future__ import annotations

import logging
import os
from concurrent import futures

import grpc

from backend.app.clients import transcribe_pb2, transcribe_pb2_grpc

LOGGER = logging.getLogger(__name__)


class ASRService(transcribe_pb2_grpc.TranscribeServicer):
    """gRPC servicer stub for the Whisper-based ASR pipeline."""

    def Run(  # type: ignore[override]
        self,
        request: transcribe_pb2.AudioRequest,
        context: grpc.ServicerContext,
    ) -> transcribe_pb2.Transcript:
        """Handle transcription requests.

        Args:
            request: Incoming gRPC request with audio metadata.
            context: gRPC request context.

        Returns:
            Placeholder transcript response until ASR logic is implemented.
        """

        context.abort(grpc.StatusCode.UNIMPLEMENTED, "ASR inference is not implemented yet.")


def _create_server(max_workers: int) -> grpc.Server:
    """Instantiate a gRPC server for the ASR service."""

    return grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))


def serve() -> None:
    """Start the ASR gRPC service."""

    logging.basicConfig(level=os.getenv("ASR_LOG_LEVEL", "INFO"))
    port = os.getenv("ASR_SERVICE_PORT", "50051")
    max_workers = int(os.getenv("ASR_MAX_WORKERS", "4"))

    server = _create_server(max_workers=max_workers)
    transcribe_pb2_grpc.add_TranscribeServicer_to_server(ASRService(), server)
    server.add_insecure_port(f"[::]:{port}")

    LOGGER.info("Starting ASR service on port %s", port)
    server.start()
    server.wait_for_termination()


def main() -> None:
    """Entrypoint for running the ASR service as a module."""

    serve()


if __name__ == "__main__":
    main()

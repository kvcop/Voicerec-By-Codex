"""ASR gRPC service bootstrap."""

from __future__ import annotations

import importlib
import logging
import os
from concurrent import futures
from functools import cache
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

    def __init__(self) -> None:
        """Initialise the Whisper model and supporting components."""
        self._model_name = _resolve_model_name()
        self._device, self._dtype_name = _resolve_device()
        LOGGER.info(
            "Loading Whisper model '%s' on device '%s' with dtype '%s'",
            self._model_name,
            self._device,
            self._dtype_name,
        )
        self._model, self._processor = _load_whisper_components(
            self._model_name,
            self._device,
            self._dtype_name,
        )

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


def _resolve_model_name() -> str:
    """Return the Whisper model identifier configured for the service."""
    requested_size = os.getenv('ASR_MODEL_SIZE', 'large-v2').strip()
    model_name = requested_size if '/' in requested_size else f'openai/whisper-{requested_size}'

    LOGGER.info('Configured Whisper model: %s', model_name)
    return model_name


def _resolve_device() -> tuple[str, str]:
    """Determine the optimal device and dtype for loading the Whisper model."""
    try:
        torch = importlib.import_module('torch')
    except ImportError as exc:  # pragma: no cover - torch is a runtime dependency
        message = 'PyTorch must be installed to run the ASR service'
        raise RuntimeError(message) from exc

    if torch.cuda.is_available():
        return 'cuda', 'float16'

    LOGGER.warning('CUDA device not available. Falling back to CPU inference for Whisper.')
    return 'cpu', 'float32'


@cache
def _load_whisper_components(
    model_name: str,
    device: str,
    dtype_name: str,
) -> tuple[object, object]:
    """Load and cache the Whisper model and processor."""
    torch = importlib.import_module('torch')
    transformers = importlib.import_module('transformers')

    dtype = getattr(torch, dtype_name)
    LOGGER.info('Loading Whisper resources (model=%s, device=%s)', model_name, device)

    model = transformers.WhisperForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=dtype,
    ).to(device)
    processor = transformers.WhisperProcessor.from_pretrained(model_name)

    return model, processor


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

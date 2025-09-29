"""Speaker diarization gRPC service bootstrap."""

from __future__ import annotations

import importlib
import json
import logging
import os
import tempfile
import threading
import time
from concurrent import futures
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn, Protocol, cast

from app.clients import diarize_pb2, diarize_pb2_grpc
from gpu_services.diarization_resources import (
    DiarizationDependencyError,
    DiarizationResourceError,
    NemoModelArtifacts,
    ensure_nemo_artifacts_available,
    load_nemo_diarization_pipeline,
)

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


@dataclass(frozen=True)
class _SegmentResult:
    """Container for intermediate diarization segment data."""

    start: float
    end: float
    speaker: str


class _Diarizer(Protocol):
    """Protocol describing the NeMo diarizer runtime interface."""

    cfg: object

    def diarize(self) -> None:
        """Execute diarization for the configured manifest."""


class _OmegaConfApi(Protocol):
    """Subset of the OmegaConf API required by the diarization loader."""

    @staticmethod
    def update(
        cfg: object,
        key: str,
        value: object,
        *,
        merge: bool = True,
    ) -> object:
        """Update configuration values in place."""


class _OmegaModule(Protocol):
    """Protocol describing the OmegaConf module surface used by the service."""

    OmegaConf: _OmegaConfApi


if TYPE_CHECKING:
    from collections.abc import Callable as TypingCallable
else:  # pragma: no cover - runtime fallback
    from collections.abc import Callable as _TypingCallableRuntime

    TypingCallable = _TypingCallableRuntime


_RTTM_MIN_FIELDS = 9
_RTTM_SPEAKER_INDEX = 7
_RTTM_START_INDEX = 3
_RTTM_DURATION_INDEX = 4


class DiarizeService(DiarizeServicer):
    """gRPC servicer implementation backed by the NeMo diarization pipeline."""

    def __init__(self) -> None:
        """Initialise the service and validate that diarization resources exist."""
        self._artifacts: NemoModelArtifacts | None = None
        self._diarizer: _Diarizer | None = None
        self._diarizer_lock = threading.Lock()
        self._initialisation_error: str | None = None

        try:
            artifacts = ensure_nemo_artifacts_available()
            self._artifacts = artifacts
        except DiarizationDependencyError as exc:
            message = (
                'Required diarization dependencies are missing. '
                'Install nemo_toolkit[asr] and omegaconf to enable diarization.'
            )
            LOGGER.error(message)
            self._initialisation_error = message
            LOGGER.debug('Dependency resolution error details', exc_info=exc)
        except DiarizationResourceError as exc:
            message = f'Diarization resources are not available: {exc}'
            LOGGER.error(message)
            self._initialisation_error = message
        else:
            try:
                loaded_diarizer = cast(
                    '_Diarizer',
                    load_nemo_diarization_pipeline(artifacts),
                )
            except (DiarizationDependencyError, DiarizationResourceError) as exc:
                message = f'Failed to load NeMo diarization pipeline: {exc}'
                LOGGER.error(message)
                self._initialisation_error = message
                LOGGER.debug('NeMo diarization initialisation error details', exc_info=exc)
            except (
                ImportError,
                AttributeError,
                FileNotFoundError,
                RuntimeError,
                TypeError,
                ValueError,
                OSError,
            ) as exc:  # pragma: no cover - defensive guard for runtime errors
                message = 'Failed to load NeMo diarization pipeline due to an unexpected error'
                LOGGER.error(message)
                self._initialisation_error = f'{message}: {exc}'
                LOGGER.debug('Unexpected diarization initialisation error details', exc_info=exc)
            else:
                self._diarizer = loaded_diarizer
                LOGGER.info('NeMo diarization pipeline successfully initialised')

    def run(
        self,
        request: AudioRequest,
        context: ServicerContext,
    ) -> DiarizationResult:
        """Handle diarization requests by running the configured pipeline.

        Args:
            request: Incoming gRPC request with audio metadata.
            context: gRPC request context.

        Returns:
            Diarization result with normalised speaker segments.
        """
        received_path = (request.path or '').strip()
        LOGGER.info('Received diarization request for path: %s', received_path or '<empty>')

        self._ensure_ready(context)
        audio_path = self._resolve_audio_path(received_path, context)
        audio_duration = self._read_audio_duration(audio_path, context)

        inference_start = time.perf_counter()
        raw_segments = self._execute_with_error_handling(audio_path, context)

        if not raw_segments:
            LOGGER.warning(
                'Diarization pipeline returned no segments for %s. Falling back to single speaker.',
                audio_path,
            )
            raw_segments = [_SegmentResult(0.0, max(audio_duration, 0.0), 'Speaker 1')]

        clipped_segments = _clip_segments_to_duration(raw_segments, audio_duration)
        normalised_segments = _normalise_speaker_labels(clipped_segments)

        inference_duration = time.perf_counter() - inference_start
        LOGGER.info(
            'Finished diarization for %s with %d segments in %.2f seconds',
            audio_path,
            len(normalised_segments),
            inference_duration,
        )

        segment_cls = getattr(diarize_pb2, 'Segment')  # noqa: B009
        result_cls = getattr(diarize_pb2, 'DiarizationResult')  # noqa: B009
        response = result_cls()
        for segment in normalised_segments:
            response.segments.append(
                segment_cls(
                    start=segment.start,
                    end=segment.end,
                    speaker=segment.speaker,
                )
            )

        return cast('DiarizationResult', response)

    def _ensure_ready(self, context: ServicerContext) -> None:
        """Validate that service dependencies were initialised correctly."""
        if self._initialisation_error is not None:
            self._abort(context, grpc.StatusCode.FAILED_PRECONDITION, self._initialisation_error)

    def _resolve_audio_path(self, received_path: str, context: ServicerContext) -> Path:
        """Normalise and validate the audio path from the request."""
        if not received_path:
            self._abort(context, grpc.StatusCode.INVALID_ARGUMENT, 'Audio path must be provided')

        audio_path = Path(received_path)
        if not audio_path.exists():
            self._abort(context, grpc.StatusCode.NOT_FOUND, f'Audio file not found: {audio_path}')
        if not audio_path.is_file():
            self._abort(
                context,
                grpc.StatusCode.INVALID_ARGUMENT,
                f'Audio path is not a file: {audio_path}',
            )

        return audio_path

    def _read_audio_duration(self, audio_path: Path, context: ServicerContext) -> float:
        """Load metadata required for fallbacks and logging."""
        try:
            return _estimate_audio_duration(audio_path)
        except FileNotFoundError:
            self._abort(context, grpc.StatusCode.NOT_FOUND, f'Audio file not found: {audio_path}')
        except Exception as exc:  # pragma: no cover - torchaudio errors are environment specific
            LOGGER.exception('Failed to inspect audio file %s', audio_path)
            self._abort(context, grpc.StatusCode.INTERNAL, f'Failed to inspect audio file: {exc}')

    def _execute_with_error_handling(
        self,
        audio_path: Path,
        context: ServicerContext,
    ) -> list[_SegmentResult]:
        """Run diarization and translate low-level errors to gRPC statuses."""
        try:
            return self._run_diarization_pipeline(audio_path)
        except DiarizationDependencyError as exc:
            LOGGER.exception('Diarization dependencies are not satisfied')
            self._abort(context, grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        except DiarizationResourceError as exc:
            LOGGER.exception('Diarization resources are misconfigured')
            self._abort(context, grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        except FileNotFoundError:
            self._abort(context, grpc.StatusCode.NOT_FOUND, f'Audio file not found: {audio_path}')
        except Exception as exc:  # pragma: no cover - defensive fallback for runtime errors
            LOGGER.exception('Unexpected error during diarization for %s', audio_path)
            self._abort(context, grpc.StatusCode.INTERNAL, f'Diarization failed: {exc}')

    def _abort(self, context: ServicerContext, code: object, message: str) -> NoReturn:
        """Abort a gRPC request and satisfy static type checkers."""
        context.abort(code, message)
        error_message = 'gRPC abort unexpectedly returned control'
        raise RuntimeError(error_message)

    Run = run

    def _run_diarization_pipeline(self, audio_path: Path) -> list[_SegmentResult]:
        """Execute the configured diarization backend for the provided audio file."""
        diarizer = self._diarizer
        if diarizer is None:
            message = 'Diarization pipeline is not initialised'
            raise DiarizationResourceError(message)

        with self._diarizer_lock:
            return _run_nemo_diarization(audio_path, diarizer)


def _run_nemo_diarization(
    audio_path: Path,
    diarizer: _Diarizer,
) -> list[_SegmentResult]:
    """Perform diarization using the NVIDIA NeMo reference pipeline."""
    omegaconf = cast('_OmegaModule', importlib.import_module('omegaconf'))

    with tempfile.TemporaryDirectory(prefix='diarize_service_') as tmp_dir:
        workdir = Path(tmp_dir)
        manifest_path = workdir / 'manifest.json'
        out_dir = workdir / 'outputs'
        out_dir.mkdir(parents=True, exist_ok=True)

        _write_manifest(manifest_path, audio_path, out_dir)
        _configure_diarizer(diarizer, manifest_path, out_dir, omegaconf)

        LOGGER.info('Running NeMo diarization for %s', audio_path)
        diarizer.diarize()

        rttm_path = _resolve_rttm_path(audio_path, out_dir)
        if not rttm_path.is_file():
            message = f'NeMo diarization did not produce an RTTM output at {rttm_path}'
            raise DiarizationResourceError(message)

        return _parse_rttm_segments(rttm_path)


def _configure_diarizer(
    diarizer: _Diarizer,
    manifest_path: Path,
    out_dir: Path,
    omegaconf: _OmegaModule,
) -> None:
    """Update the diarizer configuration with request-specific paths."""
    cfg = getattr(diarizer, 'cfg', None)
    if cfg is None:  # pragma: no cover - defensive guard for unexpected NeMo APIs
        message = 'NeMo diarizer does not expose a configuration object'
        raise DiarizationResourceError(message)

    update = omegaconf.OmegaConf.update
    errors_module = importlib.import_module('omegaconf.errors')
    base_exception_raw = getattr(errors_module, 'OmegaConfBaseException', ValueError)
    if isinstance(base_exception_raw, type) and issubclass(base_exception_raw, BaseException):
        base_exception = base_exception_raw
    else:  # pragma: no cover - fallback for unexpected OmegaConf APIs
        base_exception = ValueError

    error_types: tuple[type[BaseException], ...] = (
        base_exception,
        AttributeError,
        KeyError,
        TypeError,
    )

    _safe_update_cfg(update, cfg, 'diarizer.manifest_filepath', str(manifest_path), error_types)
    _safe_update_cfg(update, cfg, 'diarizer.out_dir', str(out_dir), error_types)
    _safe_update_cfg(
        update,
        cfg,
        'diarizer.speaker_embeddings.save_embeddings',
        False,
        error_types,
    )
    _safe_update_cfg(
        update,
        cfg,
        'diarizer.msdd_model.parameters.save_logits',
        False,
        error_types,
    )
    _safe_update_cfg(
        update,
        cfg,
        'diarizer.msdd_model.parameters.save_attention',
        False,
        error_types,
    )


def _safe_update_cfg(
    updater: TypingCallable[..., object],
    cfg: object,
    key: str,
    value: object,
    error_types: tuple[type[BaseException], ...],
) -> None:
    """Apply a configuration update while ignoring unexpected schema issues."""
    if not callable(updater):
        message = 'The OmegaConf update function must be callable'
        raise TypeError(message)

    try:
        updater(cfg, key, value, merge=True)
    except error_types as exc:  # pragma: no cover - OmegaConf internals vary by version
        LOGGER.debug('Failed to update diarizer config key %s', key, exc_info=exc)


def _write_manifest(manifest_path: Path, audio_path: Path, out_dir: Path) -> None:
    """Write a NeMo-compatible manifest file for diarization inference."""
    rttm_path = _resolve_rttm_path(audio_path, out_dir)
    uem_path = out_dir / 'pred_uems' / f'{audio_path.stem}.uem'
    uem_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        'audio_filepath': str(audio_path),
        'offset': 0,
        'duration': None,
        'label': 'infer',
        'text': '',
        'num_speakers': 0,
        'rttm_filepath': str(rttm_path),
        'uem_filepath': str(uem_path),
    }

    manifest_path.write_text(json.dumps(entry) + '\n', encoding='utf-8')


def _resolve_rttm_path(audio_path: Path, out_dir: Path) -> Path:
    """Return the location of the RTTM file produced by NeMo."""
    rttm_dir = out_dir / 'pred_rttms'
    rttm_dir.mkdir(parents=True, exist_ok=True)
    return rttm_dir / f'{audio_path.stem}.rttm'


def _parse_rttm_segments(rttm_path: Path) -> list[_SegmentResult]:
    """Parse RTTM diarization outputs into structured segment records."""
    segments: list[_SegmentResult] = []
    for line in rttm_path.read_text(encoding='utf-8').splitlines():
        parts = line.strip().split()
        if len(parts) < _RTTM_MIN_FIELDS or parts[0].upper() != 'SPEAKER':
            continue
        try:
            start = float(parts[_RTTM_START_INDEX])
            duration = float(parts[_RTTM_DURATION_INDEX])
        except ValueError:  # pragma: no cover - guards against malformed RTTM rows
            LOGGER.debug('Skipping malformed RTTM line: %s', line)
            continue

        end = start + max(duration, 0.0)
        speaker_label = (
            parts[_RTTM_SPEAKER_INDEX] if len(parts) > _RTTM_SPEAKER_INDEX else 'unknown'
        )
        segments.append(_SegmentResult(start=start, end=end, speaker=speaker_label))

    segments.sort(key=lambda item: (item.start, item.end))
    return segments


def _normalise_speaker_labels(segments: list[_SegmentResult]) -> list[_SegmentResult]:
    """Assign canonical "Speaker N" labels preserving first appearance order."""
    mapping: dict[str, str] = {}
    normalised: list[_SegmentResult] = []
    next_index = 1

    for segment in segments:
        speaker_key = segment.speaker or 'unknown'
        if speaker_key not in mapping:
            mapping[speaker_key] = f'Speaker {next_index}'
            next_index += 1

        normalised.append(
            _SegmentResult(
                start=segment.start,
                end=segment.end,
                speaker=mapping[speaker_key],
            )
        )

    return normalised


def _clip_segments_to_duration(
    segments: list[_SegmentResult],
    duration: float,
) -> list[_SegmentResult]:
    """Ensure diarization segments stay within the bounds of the audio clip."""
    if duration <= 0:
        return [
            _SegmentResult(start=max(0.0, seg.start), end=max(0.0, seg.end), speaker=seg.speaker)
            for seg in segments
        ]

    clipped: list[_SegmentResult] = []
    for segment in segments:
        start = min(max(segment.start, 0.0), duration)
        end = min(max(segment.end, start), duration)
        clipped.append(_SegmentResult(start=start, end=end, speaker=segment.speaker))

    return clipped


def _estimate_audio_duration(audio_path: Path) -> float:
    """Return the duration of the provided audio file in seconds."""
    torchaudio = importlib.import_module('torchaudio')
    info = torchaudio.info(str(audio_path))
    if info.num_frames > 0 and info.sample_rate > 0:
        return info.num_frames / float(info.sample_rate)

    waveform, sample_rate = torchaudio.load(str(audio_path))
    if waveform.size(1) == 0 or sample_rate == 0:
        return 0.0

    return waveform.size(1) / float(sample_rate)


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

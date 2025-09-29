"""Helpers for locating and initialising diarization model assets."""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable

LOGGER = logging.getLogger(__name__)

ENV_MODEL_ROOT = 'DIARIZATION_MODEL_ROOT'
ENV_CONFIG_PATH = 'DIARIZATION_CONFIG_PATH'
ENV_VAD_MODEL = 'DIARIZATION_VAD_MODEL_PATH'
ENV_SPEAKER_MODEL = 'DIARIZATION_SPEAKER_MODEL_PATH'
ENV_MSDD_MODEL = 'DIARIZATION_MSDD_MODEL_PATH'
ENV_AUTO_DOWNLOAD = 'DIARIZATION_AUTO_DOWNLOAD'

DEFAULT_MODEL_ROOT = Path(__file__).resolve().parent / 'models'
DEFAULT_CONFIG_NAME = 'diar_inference.yaml'
DEFAULT_VAD_MODEL_NAME = 'vad_multilingual_marblenet.nemo'
DEFAULT_SPEAKER_MODEL_NAME = 'titanet_large.nemo'
DEFAULT_MSDD_MODEL_NAME = 'msdd_telephonic.nemo'


class DiarizationResourceError(RuntimeError):
    """Base error for diarization resource issues."""


class DiarizationDependencyError(DiarizationResourceError):
    """Raised when required diarization dependencies are missing."""


@dataclass(frozen=True)
class NemoModelArtifacts:
    """Resolved file paths that describe a NeMo diarization deployment."""

    config_path: Path
    vad_model_path: Path
    speaker_model_path: Path
    msdd_model_path: Path | None

    def iter_required_paths(self) -> Iterable[Path]:
        """Yield all paths that must exist for the diarization pipeline."""
        yield self.config_path
        yield self.vad_model_path
        yield self.speaker_model_path
        if self.msdd_model_path is not None:
            yield self.msdd_model_path

    def validate(self) -> None:
        """Ensure that every required diarization artifact is present."""
        missing = [str(path) for path in self.iter_required_paths() if not path.is_file()]
        if missing:
            raise DiarizationResourceError('Missing diarization resources: ' + ', '.join(missing))


def _env_path(env_name: str, default: Path) -> Path:
    """Return a path from the environment or fall back to *default*."""
    override = os.getenv(env_name)
    if override:
        return Path(override).expanduser()
    return default


def discover_nemo_artifacts(model_root: Path | None = None) -> NemoModelArtifacts:
    """Resolve diarization artifact locations for the NeMo pipeline."""
    root = Path(model_root) if model_root is not None else DEFAULT_MODEL_ROOT
    root = root.expanduser()

    config_path = _env_path(ENV_CONFIG_PATH, root / DEFAULT_CONFIG_NAME)
    vad_model_path = _env_path(ENV_VAD_MODEL, root / DEFAULT_VAD_MODEL_NAME)
    speaker_model_path = _env_path(ENV_SPEAKER_MODEL, root / DEFAULT_SPEAKER_MODEL_NAME)

    msdd_override = os.getenv(ENV_MSDD_MODEL)
    if msdd_override == '':
        msdd_model_path: Path | None = None
    else:
        msdd_model_path = _env_path(ENV_MSDD_MODEL, root / DEFAULT_MSDD_MODEL_NAME)

    return NemoModelArtifacts(
        config_path=config_path,
        vad_model_path=vad_model_path,
        speaker_model_path=speaker_model_path,
        msdd_model_path=msdd_model_path,
    )


def ensure_dependencies_available() -> None:
    """Validate that Python dependencies for diarization are installed."""
    try:
        importlib.import_module('nemo.collections.asr')
        importlib.import_module('omegaconf')
    except ImportError as exc:  # pragma: no cover - runtime environment specific
        message = (
            'The NeMo diarization dependencies are missing. Install '
            "'nemo_toolkit[asr]' and 'omegaconf' to enable diarization support."
        )
        raise DiarizationDependencyError(message) from exc


def _auto_download_requested() -> bool:
    """Determine whether the user opted into automatic downloads."""
    value = os.getenv(ENV_AUTO_DOWNLOAD, '0').strip().lower()
    return value in {'1', 'true', 'yes'}


def ensure_nemo_artifacts_available(
    artifacts: NemoModelArtifacts | None = None,
) -> NemoModelArtifacts:
    """Confirm that the diarization artifacts exist on disk."""
    resolved = artifacts or discover_nemo_artifacts()
    try:
        resolved.validate()
    except DiarizationResourceError:
        if _auto_download_requested():
            LOGGER.warning(
                'Automatic diarization downloads are not implemented yet.'
                ' Please download the NeMo checkpoints manually.'
            )
        raise
    return resolved


def load_nemo_diarization_pipeline(
    artifacts: NemoModelArtifacts | None = None,
) -> object:
    """Load the NeMo diarization pipeline with the configured checkpoints."""
    ensure_dependencies_available()
    resolved = ensure_nemo_artifacts_available(artifacts)

    omegaconf = importlib.import_module('omegaconf')
    cfg = omegaconf.OmegaConf.load(resolved.config_path)
    errors_module = importlib.import_module('omegaconf.errors')
    base_exception_raw = getattr(errors_module, 'OmegaConfBaseException', ValueError)
    if isinstance(base_exception_raw, type) and issubclass(base_exception_raw, BaseException):
        base_exception = base_exception_raw
    else:  # pragma: no cover - defensive fallback for unexpected OmegaConf APIs
        base_exception = ValueError

    def _update_optional(key: str, value: str) -> None:
        try:
            omegaconf.OmegaConf.update(cfg, key, value, merge=True)
        except (base_exception, AttributeError, TypeError) as exc:  # pragma: no cover
            LOGGER.debug('Failed to update diarization config key: %s', key, exc_info=exc)

    if 'diarizer' not in cfg:  # pragma: no cover - configuration guard
        message = (
            f"Invalid diarization config: missing 'diarizer' section in {resolved.config_path}"
        )
        raise DiarizationResourceError(message)

    diarizer_module = importlib.import_module('nemo.collections.asr.models.msdd_models')
    neural_diarizer_cls = diarizer_module.NeuralDiarizer

    _update_optional('diarizer.vad.model_path', str(resolved.vad_model_path))
    _update_optional('diarizer.vad.parameters.model_path', str(resolved.vad_model_path))
    _update_optional('diarizer.speaker_embeddings.model_path', str(resolved.speaker_model_path))
    if resolved.msdd_model_path is not None:
        _update_optional('diarizer.msdd_model.model_path', str(resolved.msdd_model_path))
    else:
        _update_optional('diarizer.msdd_model.model_path', '')

    LOGGER.info('Loading NeMo diarization pipeline using config: %s', resolved.config_path)
    return neural_diarizer_cls(cfg=cfg)


__all__: Final = (
    'DiarizationDependencyError',
    'DiarizationResourceError',
    'NemoModelArtifacts',
    'discover_nemo_artifacts',
    'ensure_dependencies_available',
    'ensure_nemo_artifacts_available',
    'load_nemo_diarization_pipeline',
)

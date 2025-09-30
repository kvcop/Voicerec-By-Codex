"""Tests for the diarization gRPC service bootstrap."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

diarize_service = importlib.import_module('gpu_services.diarize_service')


class _SegmentMessageLike(Protocol):
    """Protocol representing diarization segment message objects."""

    start: float
    end: float
    speaker: str


class _DiarizationResultLike(Protocol):
    """Protocol for the diarization response object used in tests."""

    segments: list[_SegmentMessageLike]


class _DiarizeServiceLike(Protocol):
    """Protocol capturing the subset of the diarization service used in tests."""

    _diarizer: object

    def run(self, request: object, context: object) -> _DiarizationResultLike:
        """Process a diarization request and return a response."""


@dataclass(slots=True)
class _FakeContext:
    """Test double for the gRPC context that captures abort calls."""

    aborted: tuple[object, str] | None = None

    def abort(self, code: object, details: str) -> None:
        """Record abort requests and raise an error to fail the test."""
        self.aborted = (code, details)
        message = f'Unexpected gRPC abort: {code} {details}'
        raise AssertionError(message)


@dataclass(slots=True)
class _DummySegment:
    """Lightweight stand-in for diarization segment objects."""

    start: float
    end: float
    speaker: str


def _build_service(
    monkeypatch: pytest.MonkeyPatch,
    workdir: Path,
) -> _DiarizeServiceLike:
    """Create a diarization service instance with stubbed dependencies."""
    config_path = workdir / 'config.yaml'
    vad_path = workdir / 'vad.nemo'
    speaker_path = workdir / 'speaker.nemo'
    msdd_path = workdir / 'msdd.nemo'

    for file_path in (config_path, vad_path, speaker_path, msdd_path):
        file_path.write_text('placeholder', encoding='utf-8')

    artifacts = diarize_service.NemoModelArtifacts(
        config_path=config_path,
        vad_model_path=vad_path,
        speaker_model_path=speaker_path,
        msdd_model_path=msdd_path,
    )

    monkeypatch.setattr(diarize_service, 'ensure_nemo_artifacts_available', lambda: artifacts)
    monkeypatch.setattr(diarize_service, 'load_nemo_diarization_pipeline', lambda _: object())

    return diarize_service.DiarizeService()


def test_run_returns_normalised_segments(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The service should clip segments and normalise speaker labels."""
    service = _build_service(monkeypatch, tmp_path)

    audio_path = tmp_path / 'conversation.wav'
    audio_path.write_bytes(b'')

    captured: dict[str, object] = {}

    def _fake_pipeline(self: _DiarizeServiceLike, path: Path) -> list[_DummySegment]:
        captured['path'] = path
        captured['diarizer'] = getattr(self, '_diarizer', None)
        return [
            _DummySegment(start=-0.2, end=2.0, speaker='alpha'),
            _DummySegment(start=2.0, end=7.4, speaker='beta'),
            _DummySegment(start=7.4, end=8.5, speaker='alpha'),
        ]

    monkeypatch.setattr(diarize_service, '_estimate_audio_duration', lambda _: 8.0)
    monkeypatch.setattr(
        diarize_service.DiarizeService,
        '_run_diarization_pipeline',
        _fake_pipeline,
    )

    request = SimpleNamespace(path=str(audio_path))
    context = _FakeContext()

    response = service.run(request, context)

    assert captured['path'] == audio_path
    assert captured['diarizer'] is not None

    segments = [
        (pytest.approx(segment.start), pytest.approx(segment.end), segment.speaker)
        for segment in response.segments
    ]
    assert segments == [
        (pytest.approx(0.0), pytest.approx(2.0), 'Speaker 1'),
        (pytest.approx(2.0), pytest.approx(7.4), 'Speaker 2'),
        (pytest.approx(7.4), pytest.approx(8.0), 'Speaker 1'),
    ]
    assert context.aborted is None


def test_run_falls_back_to_single_speaker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When diarization returns no segments the service should synthesise one."""
    service = _build_service(monkeypatch, tmp_path)

    audio_path = tmp_path / 'short.wav'
    audio_path.write_bytes(b'')

    def _empty_pipeline(
        self: _DiarizeServiceLike,
        path: Path,
    ) -> list[_DummySegment]:
        del self, path
        return []

    monkeypatch.setattr(diarize_service, '_estimate_audio_duration', lambda _: 5.25)
    monkeypatch.setattr(
        diarize_service.DiarizeService,
        '_run_diarization_pipeline',
        _empty_pipeline,
    )

    request = SimpleNamespace(path=str(audio_path))
    context = _FakeContext()

    response = service.run(request, context)

    assert [(segment.start, segment.end, segment.speaker) for segment in response.segments] == [
        (0.0, 5.25, 'Speaker 1')
    ]
    assert context.aborted is None

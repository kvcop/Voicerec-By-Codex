"""Tests for the GPU ASR service bootstrap."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Protocol, cast

from app.clients import transcribe_pb2

EXPECTED_SAMPLE_RATE = 16_000


def _load_asr_service_module() -> ModuleType:
    """Import the ASR service module ensuring the repository root is on sys.path."""
    root_dir = Path(__file__).resolve().parents[2]
    root_str = str(root_dir)
    if root_str not in sys.path:
        sys.path.append(root_str)
    return importlib.import_module('gpu_services.asr_service')


class DummyContext:
    """Collect abort invocations without raising exceptions."""

    def __init__(self) -> None:
        self.abort_calls: list[tuple[object, str]] = []

    def abort(self, code: object, details: str) -> None:
        """Record the gRPC abort request for later inspection."""
        self.abort_calls.append((code, details))


class DummyTensor:
    """Tensor-like object that records dtype and device conversions."""

    def __init__(self) -> None:
        self.moves: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def to(self, *args: object, **kwargs: object) -> DummyTensor:
        """Mimic torch.Tensor.to by recording the provided arguments."""
        self.moves.append((args, kwargs))
        return self


class DummyWaveform:
    """Minimal waveform stub compatible with the ASR pipeline."""

    def __init__(self) -> None:
        self._samples = [0.1, 0.2, 0.3]

    def numel(self) -> int:
        """Return the number of samples in the waveform."""
        return len(self._samples)

    def squeeze(self, dim: int) -> DummySqueezed:
        """Return a squeezed view of the waveform data."""
        if dim != 0:
            message = f'Only squeeze along dimension 0 is supported, received: {dim}'
            raise AssertionError(message)
        return DummySqueezed(self._samples)


class DummySqueezed:
    """Represent a squeezed tensor that can be converted to numpy."""

    def __init__(self, samples: list[float]) -> None:
        self._samples = samples

    def numpy(self) -> list[float]:
        """Return the stored samples as a Python list."""
        return self._samples


class DummyModel:
    """Minimal Whisper-like model returning predetermined tokens."""

    device = 'cpu'

    def generate(self, input_features: DummyTensor) -> list[str]:
        """Produce deterministic tokens for testing."""
        assert isinstance(input_features, DummyTensor)
        return ['stub-tokens']


class DummyProcessor:
    """Processor stub that provides tensors and decoded text."""

    def __init__(self, tensor: DummyTensor) -> None:
        self._tensor = tensor

    def __call__(
        self,
        waveform: list[float],
        sampling_rate: int,
        return_tensors: str,
    ) -> SimpleNamespace:
        """Return the dummy tensor while validating inputs."""
        assert isinstance(waveform, list)
        assert sampling_rate == EXPECTED_SAMPLE_RATE
        assert return_tensors == 'pt'
        return SimpleNamespace(input_features=self._tensor)

    def batch_decode(self, tokens: list[str], skip_special_tokens: bool) -> list[str]:
        """Return deterministic decoded text."""
        assert tokens == ['stub-tokens']
        assert skip_special_tokens is True
        return ['привет из рум']


class MonkeyPatchProtocol(Protocol):
    """Subset of the pytest monkeypatch fixture used in this test."""

    def setattr(self, target: object, name: str, value: object) -> None:
        """Set an attribute on the target object."""


class AudioRequestFactory(Protocol):
    """Callable protocol describing the AudioRequest constructor."""

    def __call__(self, *, path: str) -> object:
        """Create an AudioRequest message."""


class TranscribeModuleProtocol(Protocol):
    """Protocol describing the subset of transcribe_pb2 used in the test."""

    AudioRequest: AudioRequestFactory


def test_asr_service_run_on_cpu(monkeypatch: MonkeyPatchProtocol, tmp_path: Path) -> None:
    """ASRService.run should transcribe audio and apply post-processing on CPU."""
    asr_service = _load_asr_service_module()

    audio_path = tmp_path / 'sample.wav'
    audio_path.write_bytes(b'fake-wav')

    dummy_tensor = DummyTensor()
    dummy_model = DummyModel()
    dummy_processor = DummyProcessor(dummy_tensor)
    context = DummyContext()

    def resolve_device() -> tuple[str, str]:
        """Force CPU inference for the test scenario."""
        return 'cpu', 'float32'

    def load_components(*_: object) -> tuple[DummyModel, DummyProcessor]:
        """Return the preconfigured model and processor pair."""
        return dummy_model, dummy_processor

    def load_waveform(_: Path) -> tuple[DummyWaveform, int]:
        """Return the deterministic waveform and sampling rate."""
        return DummyWaveform(), EXPECTED_SAMPLE_RATE

    original_import = asr_service.importlib.import_module

    def fake_import(name: str) -> object:
        """Provide a lightweight torch substitute when requested."""
        if name == 'torch':
            return SimpleNamespace(float32='float32')
        return original_import(name)

    monkeypatch.setattr(asr_service, '_resolve_device', resolve_device)
    monkeypatch.setattr(asr_service, '_load_whisper_components', load_components)
    monkeypatch.setattr(asr_service, '_load_waveform', load_waveform)
    monkeypatch.setattr(asr_service.importlib, 'import_module', fake_import)

    service = asr_service.ASRService()
    transcribe_module = cast('TranscribeModuleProtocol', transcribe_pb2)
    request_factory = transcribe_module.AudioRequest
    request = request_factory(path=str(audio_path))
    response = service.run(request, context)

    assert response.text == 'привет из RUMA'
    assert context.abort_calls == []
    assert dummy_tensor.moves == [(('cpu',), {}), ((), {'dtype': 'float32'})]

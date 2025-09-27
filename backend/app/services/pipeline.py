"""Pipeline orchestration service for gRPC-based speech processing."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from collections.abc import AsyncIterator, Awaitable

from app.core.settings import GPUSettings
from app.grpc_client import create_grpc_client
from app.services.transcript import (
    RAW_AUDIO_DIR,
    TranscriptClientProtocol,
    TranscriptService,
    resolve_transcribe_fixture_path,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DIARIZE_FIXTURE = REPO_ROOT / 'backend' / 'tests' / 'fixtures' / 'diarize.json'
DEFAULT_SUMMARIZE_FIXTURE = REPO_ROOT / 'backend' / 'tests' / 'fixtures' / 'summarize.json'


class DiarizeClientProtocol(Protocol):
    """Protocol describing diarization client behavior."""

    async def run(self, source: Path) -> dict[str, Any]:
        """Return diarization payload for the provided audio source."""

    async def stream_run(self, source: Path) -> AsyncIterator[dict[str, Any]]:
        """Yield diarization segments for streaming consumers."""


class SummarizeClientProtocol(Protocol):
    """Protocol describing summarization client behavior."""

    async def run(self, text: str) -> dict[str, Any]:
        """Return summary payload for the provided text."""

    async def stream_run(self, text: str) -> AsyncIterator[dict[str, Any]]:
        """Yield summary fragments for streaming consumers."""


class PipelineService:
    """Coordinate transcript, diarization and summarization calls."""

    def __init__(
        self,
        transcribe_client: TranscriptClientProtocol,
        diarize_client: DiarizeClientProtocol,
        summarize_client: SummarizeClientProtocol,
        *,
        raw_audio_dir: Path | None = None,
        words_per_chunk: int = 40,
    ) -> None:
        """Store dependencies for later use."""
        self._transcribe_client = transcribe_client
        self._diarize_client = diarize_client
        self._summarize_client = summarize_client
        self._raw_audio_dir = raw_audio_dir or RAW_AUDIO_DIR
        self._transcript_service = TranscriptService(
            transcribe_client,
            raw_audio_dir=self._raw_audio_dir,
            words_per_chunk=words_per_chunk,
        )

    async def stream_pipeline(self, meeting_id: str) -> AsyncIterator[dict[str, Any]]:
        """Run all pipeline steps and yield structured events."""
        audio_path = self._raw_audio_dir / f'{meeting_id}.wav'
        transcript_parts: list[str] = []

        async for chunk in self._transcript_service.stream_transcript(meeting_id):
            text = chunk.get('text')
            if isinstance(text, str):
                transcript_parts.append(text)
            else:
                segment = chunk.get('segment')
                if isinstance(segment, dict):
                    segment_text = segment.get('text')
                    if isinstance(segment_text, str):
                        transcript_parts.append(segment_text)
            yield {'type': 'transcribe', 'payload': chunk}

        iterator = await _ensure_async_iterator(self._diarize_client.stream_run(audio_path))
        async for segment in iterator:
            yield {'type': 'diarize', 'payload': segment}

        summary_input = ' '.join(transcript_parts).strip()
        summary_iterator = await _ensure_async_iterator(
            self._summarize_client.stream_run(summary_input)
        )
        async for summary_chunk in summary_iterator:
            yield {'type': 'summarize', 'payload': summary_chunk}


def _resolve_diarize_fixture_path() -> Path:
    """Determine diarization fixture path for the mock client."""
    env_path = os.getenv('DIARIZE_FIXTURE_PATH')
    if env_path:
        return Path(env_path)
    return DEFAULT_DIARIZE_FIXTURE


def _resolve_summarize_fixture_path() -> Path:
    """Determine summarize fixture path for the mock client."""
    env_path = os.getenv('SUMMARIZE_FIXTURE_PATH')
    if env_path:
        return Path(env_path)
    return DEFAULT_SUMMARIZE_FIXTURE


def get_pipeline_service(
    client_type: str | None = None,
    gpu_settings: GPUSettings | None = None,
) -> PipelineService:
    """Create pipeline service with clients resolved via the factory."""
    resolved_type = client_type or os.getenv('GRPC_CLIENT_TYPE', 'mock')
    if resolved_type == 'grpc' and gpu_settings is None:
        gpu_settings = GPUSettings()

    transcribe_client = create_grpc_client(
        'transcribe',
        resolve_transcribe_fixture_path(),
        client_type=client_type,
        gpu_settings=gpu_settings,
    )
    diarize_client = create_grpc_client(
        'diarize',
        _resolve_diarize_fixture_path(),
        client_type=client_type,
        gpu_settings=gpu_settings,
    )
    summarize_client = create_grpc_client(
        'summarize',
        _resolve_summarize_fixture_path(),
        client_type=client_type,
        gpu_settings=gpu_settings,
    )

    return PipelineService(
        cast('TranscriptClientProtocol', transcribe_client),
        cast('DiarizeClientProtocol', diarize_client),
        cast('SummarizeClientProtocol', summarize_client),
    )


__all__ = [
    'PipelineService',
    'get_pipeline_service',
]
_T = TypeVar('_T')


async def _ensure_async_iterator(
    candidate: AsyncIterator[_T] | Awaitable[AsyncIterator[_T]],
) -> AsyncIterator[_T]:
    """Return async iterator regardless of coroutine or iterator input."""
    if hasattr(candidate, '__await__'):
        awaitable = cast('Awaitable[AsyncIterator[_T]]', candidate)
        return await awaitable
    return candidate

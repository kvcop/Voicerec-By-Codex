"""Transcript streaming service implementation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
<<<<<< codex/2025-09-27-refactor-transcript-service-for-byte-streaming
    from collections.abc import AsyncGenerator, Iterable, Iterator
=======
    from collections.abc import AsyncGenerator, Iterable, Mapping
>>>>>> main

from app.core.settings import get_settings
from app.grpc_client import create_grpc_client
from app.services.meeting_processing import (
    DiarizeClientProtocol,
    MeetingProcessingResult,
    MeetingProcessingService,
    SummarizeClientProtocol,
    TranscribeClientProtocol,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TRANSCRIBE_FIXTURE = REPO_ROOT / 'backend' / 'tests' / 'fixtures' / 'transcribe.json'
DEFAULT_DIARIZE_FIXTURE = REPO_ROOT / 'backend' / 'tests' / 'fixtures' / 'diarize.json'
DEFAULT_SUMMARIZE_FIXTURE = REPO_ROOT / 'backend' / 'tests' / 'fixtures' / 'summarize.json'


def resolve_raw_audio_dir() -> Path:
    """Return directory configured for storing raw audio files."""
    directory = get_settings().raw_audio_dir
    directory.mkdir(parents=True, exist_ok=True)
    return directory


<<<<<< codex/2025-09-27-refactor-transcript-service-for-byte-streaming
class TranscriptClientProtocol(Protocol):
    """Protocol describing client required by the transcript service."""

    async def run(self, source: Iterable[bytes]) -> dict[str, Any]:
        """Return transcript payload for the provided audio source."""


=======
>>>>>> main
class MeetingNotFoundError(Exception):
    """Raised when requested meeting audio file is missing."""

    def __init__(self, meeting_id: str) -> None:
        message = f'Meeting {meeting_id} not found'
        super().__init__(message)
        self.meeting_id = meeting_id


class TranscriptService:
    """Stream transcript fragments for SSE consumption."""

    def __init__(
        self,
        meeting_processor: MeetingProcessingService,
        *,
        raw_audio_dir: Path | None = None,
<<<<<< codex/2025-09-27-refactor-transcript-service-for-byte-streaming
        words_per_chunk: int = 40,
        audio_chunk_size: int = 64 * 1024,
=======
>>>>>> main
    ) -> None:
        """Initialize the service.

        Args:
            meeting_processor: Service responsible for aggregating meeting data.
            raw_audio_dir: Directory where meeting audio files are stored.
<<<<<< codex/2025-09-27-refactor-transcript-service-for-byte-streaming
            words_per_chunk: Number of words per streamed chunk.
            audio_chunk_size: Number of bytes read per chunk when streaming audio.
        """
        if words_per_chunk <= 0:
            message = 'words_per_chunk must be positive'
            raise ValueError(message)

        if audio_chunk_size <= 0:
            message = 'audio_chunk_size must be positive'
            raise ValueError(message)

        self._client = transcript_client
        self._raw_audio_dir = raw_audio_dir or resolve_raw_audio_dir()
        self._words_per_chunk = words_per_chunk
        self._audio_chunk_size = audio_chunk_size
=======
        """
        self._meeting_processor = meeting_processor
        self._raw_audio_dir = raw_audio_dir or resolve_raw_audio_dir()
>>>>>> main

    async def stream_transcript(self, meeting_id: str) -> AsyncGenerator[StreamItem, None]:
        """Yield meeting events and final summary for the provided meeting.

        Args:
            meeting_id: Identifier of the meeting whose transcript should be streamed.

        Yields:
            Dictionaries describing SSE events.
        """
        audio_path = self._resolve_audio_path(meeting_id)
<<<<<< codex/2025-09-27-refactor-transcript-service-for-byte-streaming
        payload = await self._client.run(self._read_audio_bytes(audio_path))
=======
        result = await self._meeting_processor.process(audio_path)
>>>>>> main

        for item in self._yield_transcript_events(result):
            yield item
        yield self._build_summary_item(result)

    def ensure_audio_available(self, meeting_id: str) -> None:
        """Validate that raw audio exists for the provided meeting identifier."""
        self._resolve_audio_path(meeting_id)

    def audio_exists(self, meeting_id: str) -> bool:
        """Return whether audio for the provided meeting id is available."""
        return (self._raw_audio_dir / f'{meeting_id}.wav').is_file()

    def _resolve_audio_path(self, meeting_id: str) -> Path:
        """Return audio file path and ensure it exists."""
        audio_path = self._raw_audio_dir / f'{meeting_id}.wav'
        if not audio_path.is_file():
            raise MeetingNotFoundError(meeting_id)
        return audio_path

    def _yield_transcript_events(self, result: MeetingProcessingResult) -> Iterable[StreamItem]:
        """Return transcript events for the SSE stream."""
        for event in result.events:
            yield {'event': 'transcript', 'data': event}

    def _build_summary_item(self, result: MeetingProcessingResult) -> StreamItem:
        """Return final summary SSE payload."""
        return {'event': 'summary', 'data': {'summary': result.summary}}

    def _read_audio_bytes(self, audio_path: Path) -> Iterable[bytes]:
        """Return generator that yields audio file bytes."""

        def _iterator() -> Iterator[bytes]:
            with audio_path.open('rb') as audio_file:
                while chunk := audio_file.read(self._audio_chunk_size):
                    yield chunk

        return _iterator()


def _resolve_fixture_path() -> Path:
    """Determine transcript fixture path for the mock gRPC client."""
    env_path = os.getenv('TRANSCRIBE_FIXTURE_PATH')
    if env_path:
        return Path(env_path)
    return DEFAULT_TRANSCRIBE_FIXTURE


def _resolve_diarize_fixture_path() -> Path:
    """Determine diarization fixture path for the mock gRPC client."""
    env_path = os.getenv('DIARIZE_FIXTURE_PATH')
    if env_path:
        return Path(env_path)
    return DEFAULT_DIARIZE_FIXTURE


def _resolve_summarize_fixture_path() -> Path:
    """Determine summarize fixture path for the mock gRPC client."""
    env_path = os.getenv('SUMMARIZE_FIXTURE_PATH')
    if env_path:
        return Path(env_path)
    return DEFAULT_SUMMARIZE_FIXTURE


def get_transcript_service() -> TranscriptService:
    """Return transcript service instance configured with mock gRPC client."""
    transcribe_fixture = _resolve_fixture_path()
    diarize_fixture = _resolve_diarize_fixture_path()
    summarize_fixture = _resolve_summarize_fixture_path()

    transcribe_client = create_grpc_client('transcribe', transcribe_fixture)
    diarize_client = create_grpc_client('diarize', diarize_fixture)
    summarize_client = create_grpc_client('summarize', summarize_fixture)

    processor = MeetingProcessingService(
        cast('TranscribeClientProtocol', transcribe_client),
        cast('DiarizeClientProtocol', diarize_client),
        cast('SummarizeClientProtocol', summarize_client),
    )
    return TranscriptService(processor)


class StreamItem(TypedDict):
    """Structured representation of SSE events emitted by the service."""

    event: Literal['transcript', 'summary']
    data: Mapping[str, Any]

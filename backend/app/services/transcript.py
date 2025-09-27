"""Transcript streaming service implementation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal, TypedDict, cast

if TYPE_CHECKING:  # pragma: no cover - imports for typing only
    from collections.abc import AsyncGenerator, Iterable, Mapping

    from sqlalchemy.ext.asyncio import AsyncSession
else:  # pragma: no cover - define runtime reference for dependency evaluation
    import sqlalchemy.ext.asyncio as _sqlalchemy_asyncio

    AsyncSession = _sqlalchemy_asyncio.AsyncSession

from fastapi import Depends

from app.core.settings import GPUSettings, get_settings
from app.db.session import get_session
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


class MeetingNotFoundError(Exception):
    """Raised when requested meeting audio file is missing."""

    def __init__(self, meeting_id: str) -> None:
        message = f'Meeting {meeting_id} not found'
        super().__init__(message)
        self.meeting_id = meeting_id


class StreamItem(TypedDict):
    """Structured representation of SSE events emitted by the service."""

    event: Literal['transcript', 'summary']
    data: Mapping[str, Any]


class TranscriptService:
    """Stream transcript fragments for SSE consumption."""

    def __init__(
        self,
        session: AsyncSession,
        meeting_processor: MeetingProcessingService,
        *,
        raw_audio_dir: Path | None = None,
        enforce_audio_presence: bool = True,
    ) -> None:
        """Initialize the service.

        Args:
            session: Database session used for persisting transcript data.
            meeting_processor: Service responsible for aggregating meeting data.
            raw_audio_dir: Directory where meeting audio files are stored.
            enforce_audio_presence: Whether to ensure audio exists before processing.
        """
        self._session = session
        self._meeting_processor = meeting_processor
        self._raw_audio_dir = raw_audio_dir or resolve_raw_audio_dir()
        self._enforce_audio_presence = enforce_audio_presence

    async def stream_transcript(self, meeting_id: str) -> AsyncGenerator[StreamItem, None]:
        """Yield meeting events and final summary for the provided meeting.

        Args:
            meeting_id: Identifier of the meeting whose transcript should be streamed.

        Yields:
            Stream items describing SSE events.
        """
        audio_path = self._resolve_audio_path(meeting_id)
        result = await self._meeting_processor.process(audio_path)

        for item in self._yield_transcript_events(result):
            yield item
        yield self._build_summary_item(result)

    def ensure_audio_available(self, meeting_id: str) -> None:
        """Validate that raw audio exists for the provided meeting identifier."""
        self._resolve_audio_path(meeting_id)

    def _resolve_audio_path(self, meeting_id: str) -> Path:
        """Return audio file path and ensure it exists when enforcement is enabled."""
        audio_path = self._raw_audio_dir / f'{meeting_id}.wav'
        if self._enforce_audio_presence and not audio_path.is_file():
            raise MeetingNotFoundError(meeting_id)
        return audio_path

    def _yield_transcript_events(self, result: MeetingProcessingResult) -> Iterable[StreamItem]:
        """Return transcript events for the SSE stream."""
        for event in result.events:
            yield {'event': 'transcript', 'data': event}

    def _build_summary_item(self, result: MeetingProcessingResult) -> StreamItem:
        """Return final summary SSE payload."""
        return {'event': 'summary', 'data': {'summary': result.summary}}

    @property
    def session(self) -> AsyncSession:
        """Return session used by the service."""
        return self._session

    @property
    def raw_audio_dir(self) -> Path:
        """Return directory where raw audio files are stored."""
        return self._raw_audio_dir


def resolve_transcribe_fixture_path() -> Path:
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


def get_transcript_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    client_type: str | None = None,
    gpu_settings: GPUSettings | None = None,
    raw_audio_dir: Path | None = None,
    enforce_audio_presence: bool | None = None,
) -> TranscriptService:
    """Return transcript service instance configured with selected gRPC client."""
    resolved_type = client_type or os.getenv('GRPC_CLIENT_TYPE', 'mock')
    if resolved_type == 'grpc' and gpu_settings is None:
        gpu_settings = GPUSettings()

    if enforce_audio_presence is None:
        enforce_audio_presence = resolved_type != 'mock'

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

    processor = MeetingProcessingService(
        cast('TranscribeClientProtocol', transcribe_client),
        cast('DiarizeClientProtocol', diarize_client),
        cast('SummarizeClientProtocol', summarize_client),
    )
    return TranscriptService(
        session,
        processor,
        raw_audio_dir=raw_audio_dir,
        enforce_audio_presence=enforce_audio_presence,
    )


__all__ = [
    'MeetingNotFoundError',
    'StreamItem',
    'TranscriptService',
    'get_transcript_service',
    'resolve_raw_audio_dir',
    'resolve_transcribe_fixture_path',
]

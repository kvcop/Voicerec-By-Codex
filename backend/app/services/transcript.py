"""Transcript streaming service implementation."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal, TypedDict, cast
from uuid import UUID

if TYPE_CHECKING:  # pragma: no cover - imports for typing only
    from collections.abc import AsyncIterable, AsyncIterator, Iterable, Mapping

    from sqlalchemy.ext.asyncio import AsyncSession
else:  # pragma: no cover - define runtime reference for dependency evaluation
    import sqlalchemy.ext.asyncio as _sqlalchemy_asyncio

    AsyncSession = _sqlalchemy_asyncio.AsyncSession

from fastapi import Depends
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import GPUSettings, get_settings
from app.db.repositories import MeetingRepository, TranscriptRepository
from app.db.session import get_session
from app.grpc_client import create_grpc_client
from app.models.meeting import Meeting, MeetingStatus
from app.models.transcript import Transcript
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

    def stream_transcript(self, meeting_id: str) -> AsyncIterable[StreamItem]:
        """Return async iterable that yields transcript fragments and the summary.

        Args:
            meeting_id: Identifier of the meeting whose transcript should be streamed.

        Returns:
            Asynchronous iterable producing transcript and summary stream items.
        """

        async def iterator() -> AsyncIterator[StreamItem]:
            meeting_uuid = self._parse_meeting_id(meeting_id)
            audio_path = self._resolve_audio_path(meeting_id)
            try:
                result = await self._meeting_processor.process(audio_path)
            except Exception:
                await self._mark_meeting_failed(meeting_uuid)
                raise

            try:
                await self._persist_processing_result(meeting_uuid, result)
            except Exception:
                await self._mark_meeting_failed(meeting_uuid)
                raise

            for item in self._yield_transcript_events(result):
                yield item
            yield self._build_summary_item(result)

        return iterator()

    def ensure_audio_available(self, meeting_id: str) -> None:
        """Validate that raw audio exists for the provided meeting identifier."""
        self._resolve_audio_path(meeting_id)

    def enforce_audio_presence(self) -> None:
        """Enable strict audio existence validation for subsequent checks."""
        self._enforce_audio_presence = True

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

    def _parse_meeting_id(self, meeting_id: str) -> UUID:
        """Return UUID constructed from the provided meeting identifier."""
        try:
            return UUID(meeting_id)
        except ValueError as exc:
            raise MeetingNotFoundError(meeting_id) from exc

    async def _persist_processing_result(
        self, meeting_uuid: UUID, result: MeetingProcessingResult
    ) -> None:
        """Store transcript fragments and final summary in the database."""
        repository = MeetingRepository(self._session)
        meeting = await repository.get_by_id(meeting_uuid)
        if meeting is None:
            raise MeetingNotFoundError(str(meeting_uuid))

        transcript_repository = TranscriptRepository(self._session)

        async with self._session.begin():
            await self._delete_existing_transcripts(meeting_uuid)
            await self._store_transcript_events(
                meeting,
                meeting_uuid,
                result,
                transcript_repository,
            )
            await repository.update(
                meeting,
                status=MeetingStatus.COMPLETED,
                summary=self._normalize_summary(result.summary),
            )

    async def _store_transcript_events(
        self,
        meeting: Meeting,
        meeting_uuid: UUID,
        result: MeetingProcessingResult,
        repository: TranscriptRepository,
    ) -> None:
        """Persist transcript events as individual rows."""
        for event in result.events:
            speaker = event.get('speaker')
            text = event.get('text')
            if not isinstance(speaker, str) or not isinstance(text, str):
                continue
            timestamp = self._build_event_timestamp(meeting, event)
            await repository.create(
                meeting_id=meeting_uuid,
                text=text,
                speaker_id=speaker,
                timestamp=timestamp,
            )

    async def _delete_existing_transcripts(self, meeting_uuid: UUID) -> None:
        """Remove previously stored transcripts for the meeting."""
        statement = delete(Transcript).where(Transcript.meeting_id == meeting_uuid)
        await self._session.execute(statement)

    def _build_event_timestamp(self, meeting: Meeting, event: Mapping[str, Any]) -> datetime | None:
        """Return timestamp for the transcript event when offsets are available."""
        created_at = meeting.created_at
        start = event.get('start')
        if created_at is None or not isinstance(start, (int, float)):
            return None
        return created_at + timedelta(seconds=start)

    async def _mark_meeting_failed(self, meeting_uuid: UUID) -> None:
        """Set meeting status to failed when processing cannot complete."""
        await self._session.rollback()
        repository = MeetingRepository(self._session)
        meeting = await repository.get_by_id(meeting_uuid)
        if meeting is None:
            return
        try:
            async with self._session.begin():
                await repository.update(meeting, status=MeetingStatus.FAILED, summary=None)
        except SQLAlchemyError:
            await self._session.rollback()

    def _normalize_summary(self, summary: str) -> str | None:
        """Return a cleaned summary value suitable for persistence."""
        cleaned = summary.strip()
        return cleaned or None


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

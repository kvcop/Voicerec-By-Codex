"""Meeting-related API routes."""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import json
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, cast
from uuid import UUID

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_serializer

from app.api.dependencies import get_current_user
from app.db.repositories import MeetingRepository
from app.db.session import get_session
from app.models.meeting import Meeting, MeetingStatus
from app.services.transcript import (
    MeetingNotFoundError,
    StreamItem,
    TranscriptService,
    get_transcript_service,
    resolve_raw_audio_dir,
)

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from collections.abc import AsyncGenerator, AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User
else:
    AsyncSession = Any
    User = Any

router = APIRouter(prefix='/api/meeting')
legacy_router = APIRouter()

CHUNK_SIZE = 1024 * 1024
SUMMARY_SNIPPET_MAX_LENGTH = 160
ALLOWED_WAV_MIME_TYPES = {
    'audio/wav',
    'audio/x-wav',
    'audio/vnd.wave',
    'audio/wave',
}


class MeetingSummaryResponse(BaseModel):
    """Serialized representation of a meeting for list views."""

    id: str = Field(description='Unique identifier of the meeting')
    filename: str = Field(description='Original name of the uploaded audio file')
    created_at: dt.datetime = Field(description='Timestamp when the meeting was created')
    status: MeetingStatus = Field(description='Current processing status of the meeting')
    summary: str | None = Field(
        default=None, description='Short summary snippet of the meeting if available'
    )

    @classmethod
    def from_model(cls, meeting: Meeting) -> MeetingSummaryResponse:
        """Create response object from a ``Meeting`` ORM instance."""
        return cls(
            id=str(meeting.id),
            filename=meeting.filename,
            created_at=meeting.created_at,
            status=meeting.status,
            summary=_build_summary_snippet(meeting.summary),
        )

    @field_serializer('created_at')
    def _serialize_created_at(self, value: dt.datetime) -> str:
        """Serialize ``created_at`` timestamps to ISO-8601 strings."""
        if not isinstance(value, dt.datetime):
            message = 'created_at must be a datetime instance'
            raise TypeError(message)
        return value.isoformat()


def _build_summary_snippet(summary: str | None) -> str | None:
    """Return shortened summary text capped at ``SUMMARY_SNIPPET_MAX_LENGTH`` characters."""
    if summary is None:
        return None
    snippet = summary.strip()
    if len(snippet) <= SUMMARY_SNIPPET_MAX_LENGTH:
        return snippet
    truncated = snippet[: SUMMARY_SNIPPET_MAX_LENGTH - 1].rstrip()
    return f'{truncated}…'


def get_raw_audio_dir() -> Path:
    """Return configured directory for storing raw audio files."""
    directory = resolve_raw_audio_dir()
    return Path(directory)


# Allow overriding gRPC client implementation via query parameter.
ClientTypeParam = Annotated[str | None, Query(alias='client_type')]


def _transcript_service_dependency(
    base_service: Annotated[TranscriptService, Depends(get_transcript_service)],
    client_type: ClientTypeParam = None,
) -> TranscriptService:
    """Resolve transcript service with optional client type override."""
    if client_type is not None:
        return get_transcript_service(
            session=base_service.session,
            client_type=client_type,
            raw_audio_dir=base_service.raw_audio_dir,
            enforce_audio_presence=True,
        )
    if hasattr(base_service, 'enforce_audio_presence'):
        base_service.enforce_audio_presence()
    return base_service


@router.get('', response_model=list[MeetingSummaryResponse])
async def list_meetings(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MeetingSummaryResponse]:
    """Return meetings that belong to the authenticated user."""
    repository = MeetingRepository(session)
    meetings = await repository.list_by_user(current_user.id)
    return [MeetingSummaryResponse.from_model(item) for item in meetings]


@router.post('/upload')
async def upload_audio(
    file: Annotated[UploadFile, File(...)],
    raw_audio_dir: Annotated[Path, Depends(get_raw_audio_dir)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    """Save uploaded WAV file and return meeting identifier."""
    _ = current_user.id  # Access attribute to mark the dependency as used.
    content_type = (file.content_type or '').lower()
    if content_type not in ALLOWED_WAV_MIME_TYPES:
        raise HTTPException(
            status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            detail='Only WAV audio is supported.',
        )

    repository = MeetingRepository(session)
    filename = file.filename or 'meeting.wav'
    meeting = await repository.create(user_id=current_user.id, filename=filename)
    meeting_id = str(meeting.id)
    dest = raw_audio_dir / f'{meeting_id}.wav'
    # TODO: перенести в защищённое хранилище
    try:
        await _store_upload(file, dest)
    except Exception:
        await session.rollback()
        with contextlib.suppress(FileNotFoundError):
            dest.unlink(missing_ok=True)
        raise
    else:
        await session.commit()
    return {'meeting_id': meeting_id}


async def _store_upload(file: UploadFile, destination: Path) -> None:
    """Persist uploaded file to the destination path chunk by chunk."""
    try:
        async with aiofiles.open(destination, 'wb') as buffer:
            async for chunk in _iter_upload_file(file):
                await buffer.write(chunk)
    finally:
        await file.close()


async def _iter_upload_file(file: UploadFile, chunk_size: int = CHUNK_SIZE) -> AsyncIterator[bytes]:
    """Yield chunks from upload without loading entire file into memory."""
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        yield chunk


async def _event_generator(
    meeting_id: str,
    service: TranscriptService,
    *,
    heartbeat_interval: float | None = None,
    stream_timeout: float | None = None,
) -> AsyncGenerator[str, None]:
    interval = HEARTBEAT_INTERVAL_SECONDS if heartbeat_interval is None else heartbeat_interval
    timeout = STREAM_IDLE_TIMEOUT_SECONDS if stream_timeout is None else stream_timeout

    stream = service.stream_transcript(meeting_id)
    iterator = stream.__aiter__()
    loop = asyncio.get_running_loop()
    last_event_time = loop.time()
    pending: asyncio.Task[StreamItem] | None = None

    try:
        while True:
            if pending is None:
                pending = asyncio.create_task(_anext(iterator))

            done, _ = await asyncio.wait({pending}, timeout=interval)
            if not done:
                now = loop.time()
                if timeout is not None and now - last_event_time >= timeout:
                    break
                yield HEARTBEAT_COMMENT
                continue

            task = done.pop()
            pending = None
            try:
                item = task.result()
            except StopAsyncIteration:
                break

            last_event_time = loop.time()
            yield _serialize_stream_item(cast('StreamItem', item))
    finally:
        if pending is not None and not pending.done():
            pending.cancel()
            with contextlib.suppress(Exception):
                await pending
        await _close_async_iterator(iterator)


@router.get('/{meeting_id}/stream')
async def stream_transcript(
    meeting_id: str,
    service: Annotated[TranscriptService, Depends(_transcript_service_dependency)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StreamingResponse:
    """Stream transcript updates via SSE."""
    repository = MeetingRepository(session)
    meeting = await _ensure_meeting_access(meeting_id, current_user, repository)
    await _mark_meeting_processing(meeting, repository, session)
    return _streaming_response(meeting_id, service)


@legacy_router.get('/stream/{meeting_id}', include_in_schema=False)
async def stream_transcript_legacy(
    meeting_id: str,
    service: Annotated[TranscriptService, Depends(get_transcript_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StreamingResponse:
    """Legacy path kept for backward compatibility with early clients."""
    repository = MeetingRepository(session)
    meeting = await _ensure_meeting_access(meeting_id, current_user, repository)
    await _mark_meeting_processing(meeting, repository, session)
    return _streaming_response(meeting_id, service)


def _streaming_response(meeting_id: str, service: TranscriptService) -> StreamingResponse:
    """Return streaming response after verifying audio availability."""
    try:
        service.ensure_audio_available(meeting_id)
    except MeetingNotFoundError as exc:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=str(exc),
        ) from exc
    return StreamingResponse(
        _event_generator(meeting_id, service),
        media_type='text/event-stream',
    )


def _serialize_stream_item(item: StreamItem) -> str:
    """Format a service stream item to SSE-compatible payload."""
    data = json.dumps(item['data'], ensure_ascii=False)
    return f'event: {item["event"]}\ndata: {data}\n\n'


async def _close_async_iterator(iterator: AsyncIterator[StreamItem]) -> None:
    """Close asynchronous iterator if it exposes an ``aclose`` coroutine."""
    aclose = getattr(iterator, 'aclose', None)
    if aclose is None:
        return

    try:
        await aclose()
    except (RuntimeError, StopAsyncIteration):
        # Iterator may already be closed or exhausted; ignore such errors.
        return


async def _anext(iterator: AsyncIterator[StreamItem]) -> StreamItem:
    """Return next item from asynchronous iterator."""
    return await iterator.__anext__()


async def _ensure_meeting_access(
    meeting_id: str,
    current_user: User,
    repository: MeetingRepository,
) -> Meeting:
    """Return meeting if it exists and belongs to the current user."""
    try:
        meeting_uuid = UUID(meeting_id)
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Meeting not found') from exc

    meeting = await repository.get_by_id(meeting_uuid)
    if meeting is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Meeting not found')

    if meeting.user_id != current_user.id:
        detail = 'You do not have access to this meeting'
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=detail)
    return meeting


async def _mark_meeting_processing(
    meeting: Meeting,
    repository: MeetingRepository,
    session: AsyncSession,
) -> None:
    """Mark meeting as processing when transcript streaming starts."""
    if meeting.status == MeetingStatus.PROCESSING:
        return
    if meeting.status != MeetingStatus.PENDING:
        return

    await repository.update(meeting, status=MeetingStatus.PROCESSING)
    await session.commit()


__all__ = ['legacy_router', 'router']
HEARTBEAT_COMMENT = ': heartbeat\n\n'
HEARTBEAT_INTERVAL_SECONDS = 15.0
STREAM_IDLE_TIMEOUT_SECONDS = 60.0

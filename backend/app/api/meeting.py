"""Meeting-related API routes."""

from __future__ import annotations

import asyncio
import contextlib
import json
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, cast
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.services.transcript import (
    MeetingNotFoundError,
    StreamItem,
    TranscriptService,
    get_transcript_service,
    resolve_raw_audio_dir,
)

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from collections.abc import AsyncGenerator, AsyncIterator

router = APIRouter(prefix='/api/meeting')
legacy_router = APIRouter()

CHUNK_SIZE = 1024 * 1024
ALLOWED_WAV_MIME_TYPES = {
    'audio/wav',
    'audio/x-wav',
    'audio/vnd.wave',
    'audio/wave',
}


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
        )
    return base_service


@router.post('/upload')
async def upload_audio(
    file: Annotated[UploadFile, File(...)],
    raw_audio_dir: Annotated[Path, Depends(get_raw_audio_dir)],
) -> dict[str, str]:
    """Save uploaded WAV file and return meeting identifier."""
    content_type = (file.content_type or '').lower()
    if content_type not in ALLOWED_WAV_MIME_TYPES:
        raise HTTPException(
            status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            detail='Only WAV audio is supported.',
        )

    meeting_id = uuid4().hex
    dest = raw_audio_dir / f'{meeting_id}.wav'
    # TODO: перенести в защищённое хранилище
    await _store_upload(file, dest)
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
) -> StreamingResponse:
    """Stream transcript updates via SSE."""
    return _streaming_response(meeting_id, service)


@legacy_router.get('/stream/{meeting_id}', include_in_schema=False)
async def stream_transcript_legacy(
    meeting_id: str,
    service: Annotated[TranscriptService, Depends(get_transcript_service)],
) -> StreamingResponse:
    """Legacy path kept for backward compatibility with early clients."""
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


__all__ = ['legacy_router', 'router']
HEARTBEAT_COMMENT = ': heartbeat\n\n'
HEARTBEAT_INTERVAL_SECONDS = 15.0
STREAM_IDLE_TIMEOUT_SECONDS = 60.0

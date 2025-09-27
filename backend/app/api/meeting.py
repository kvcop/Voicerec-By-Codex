"""Meeting-related API routes."""

from __future__ import annotations

import json
import pathlib
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.services.transcript import (
<<<<<< codex/2025-09-27-check-and-complete-task-a3
    MeetingNotFoundError,
    TranscriptService,
    get_transcript_service,
    resolve_raw_audio_dir,
=======
    RAW_AUDIO_DIR,
    MeetingNotFoundError,
    TranscriptService,
    get_transcript_service,
>>>>>> main
)

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from collections.abc import AsyncGenerator, AsyncIterator

router = APIRouter(prefix='/api/meeting')

CHUNK_SIZE = 1024 * 1024
ALLOWED_WAV_MIME_TYPES = {
    'audio/wav',
    'audio/x-wav',
    'audio/vnd.wave',
    'audio/wave',
}


def get_raw_audio_dir() -> pathlib.Path:
    """Return configured directory for storing raw audio files."""
    directory = resolve_raw_audio_dir()
    return pathlib.Path(directory)


@router.post('/upload')
async def upload_audio(
    file: Annotated[UploadFile, File(...)],
    raw_audio_dir: Annotated[pathlib.Path, Depends(get_raw_audio_dir)],
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


async def _store_upload(file: UploadFile, destination: pathlib.Path) -> None:
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
    meeting_id: str, service: TranscriptService
) -> AsyncGenerator[str, None]:
    async for payload in service.stream_transcript(meeting_id):
        yield f'data: {json.dumps(payload, ensure_ascii=False)}\n\n'
    yield 'event: end\ndata: {}\n\n'


@router.get('/{meeting_id}/stream')
async def stream_transcript(
    meeting_id: str,
    service: Annotated[TranscriptService, Depends(get_transcript_service)],
) -> StreamingResponse:
    """Stream transcript updates via SSE."""
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

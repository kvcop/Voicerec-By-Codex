"""Meeting-related API routes."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse

from app.services.transcript import RAW_AUDIO_DIR, TranscriptService, get_transcript_service

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from collections.abc import AsyncGenerator

router = APIRouter()

CHUNK_SIZE = 1024 * 1024

# Directory for raw audio files.
RAW_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@router.post('/upload')
async def upload_audio(file: Annotated[UploadFile, File(...)]) -> dict[str, str]:
    """Save uploaded WAV file and return meeting identifier."""
    meeting_id = uuid4().hex
    dest = RAW_AUDIO_DIR / f'{meeting_id}.wav'
    # TODO: перенести в защищённое хранилище
    async with aiofiles.open(dest, 'wb') as buffer:
        try:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                await buffer.write(chunk)
        finally:
            await file.close()
    return {'meeting_id': meeting_id}


async def _event_generator(
    meeting_id: str, service: TranscriptService
) -> AsyncGenerator[str, None]:
    async for payload in service.stream_transcript(meeting_id):
        yield f'data: {json.dumps(payload, ensure_ascii=False)}\n\n'
    yield 'event: end\ndata: {}\n\n'


@router.get('/stream/{meeting_id}')
async def stream_transcript(
    meeting_id: str,
    service: Annotated[TranscriptService, Depends(get_transcript_service)],
) -> StreamingResponse:
    """Stream transcript updates via SSE."""
    return StreamingResponse(
        _event_generator(meeting_id, service),
        media_type='text/event-stream',
    )

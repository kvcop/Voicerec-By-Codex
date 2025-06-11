"""Meeting-related API routes."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from collections.abc import AsyncGenerator

router = APIRouter()

# Directory for raw audio files.
RAW_DATA_DIR = Path(__file__).resolve().parents[2] / 'data' / 'raw'
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


@router.post('/upload')
async def upload_audio(file: Annotated[UploadFile, File(...)]) -> dict[str, str]:
    """Save uploaded WAV file and return meeting identifier."""
    meeting_id = uuid4().hex
    dest = RAW_DATA_DIR / f'{meeting_id}.wav'
    # TODO: перенести в защищённое хранилище
    with dest.open('wb') as buffer:
        buffer.write(await file.read())
    return {'meeting_id': meeting_id}


async def _event_generator(
    meeting_id: str, service: TranscriptService
) -> AsyncGenerator[str, None]:
    async for text in service.stream_transcript(meeting_id):
        yield f'data: {text}\n\n'


@router.get('/stream/{meeting_id}')
async def stream_transcript(meeting_id: str) -> StreamingResponse:
    """Stream transcript updates via SSE."""
    service = TranscriptService()
    return StreamingResponse(_event_generator(meeting_id, service), media_type='text/event-stream')


class TranscriptService:
    """Service layer for transcript streaming."""

    async def stream_transcript(self, meeting_id: str) -> AsyncGenerator[str, None]:
        """Yield transcript fragments for the given meeting."""
        if False:  # pragma: no cover - placeholder for real implementation
            yield meeting_id
        return

"""Transcript service for meeting streaming."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from fastapi import Depends

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class TranscriptRepositoryProtocol(Protocol):
    """Interface for working with transcript persistence."""

    async def save_fragment(self, meeting_id: str, text: str) -> None:
        """Persist a transcript fragment for a meeting."""


class TranscribeClientProtocol(Protocol):
    """Interface for running transcription jobs."""

    async def run(self, audio_path: Path) -> dict[str, Any]:
        """Execute transcription for the provided audio path."""


class _NullTranscriptRepository:
    """Stub repository used until real implementation is provided."""

    async def save_fragment(  # pragma: no cover - placeholder
        self, _meeting_id: str, _text: str
    ) -> None:
        del _meeting_id, _text


class _NullTranscribeClient:
    """Stub gRPC client used until real implementation is provided."""

    async def run(self, audio_path: Path) -> dict[str, Any]:  # pragma: no cover - placeholder
        return {'meeting_id': audio_path.stem, 'chunks': []}


def get_transcript_repository() -> TranscriptRepositoryProtocol:
    """Provide transcript repository dependency."""
    return _NullTranscriptRepository()


def get_transcribe_client() -> TranscribeClientProtocol:
    """Provide transcribe gRPC client dependency."""
    return _NullTranscribeClient()


class TranscriptService:
    """Service layer responsible for transcript streaming logic."""

    def __init__(
        self,
        transcript_repository: TranscriptRepositoryProtocol,
        transcribe_client: TranscribeClientProtocol,
    ) -> None:
        self._transcript_repository = transcript_repository
        self._transcribe_client = transcribe_client

    async def stream_transcript(self, meeting_id: str) -> AsyncGenerator[str, None]:
        """Yield transcript fragments for the given meeting."""
        if False:  # pragma: no cover - placeholder for real implementation
            await self._transcript_repository.save_fragment(meeting_id, '')
            await self._transcribe_client.run(Path())
            yield meeting_id
        return


def get_transcript_service(
    transcript_repository: TranscriptRepositoryProtocol = Depends(get_transcript_repository),
    transcribe_client: TranscribeClientProtocol = Depends(get_transcribe_client),
) -> TranscriptService:
    """Return transcript service wired with required dependencies."""
    return TranscriptService(transcript_repository, transcribe_client)

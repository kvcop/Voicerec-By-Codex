"""Transcript streaming service implementation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from collections.abc import AsyncGenerator, Iterable

from app.core.settings import GPUSettings
from app.grpc_client import create_grpc_client

REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_AUDIO_DIR = REPO_ROOT / 'data' / 'raw'
RAW_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_TRANSCRIBE_FIXTURE = REPO_ROOT / 'backend' / 'tests' / 'fixtures' / 'transcribe.json'


class TranscriptClientProtocol(Protocol):
    """Protocol describing client required by the transcript service."""

    async def run(self, source: Path) -> dict[str, Any]:
        """Return transcript payload for the provided audio source."""


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
        transcript_client: TranscriptClientProtocol,
        *,
        raw_audio_dir: Path | None = None,
        words_per_chunk: int = 40,
        enforce_audio_presence: bool = True,
    ) -> None:
        """Initialize the service.

        Args:
            transcript_client: Client responsible for running transcription.
            raw_audio_dir: Directory where meeting audio files are stored.
            words_per_chunk: Number of words per streamed chunk.
            enforce_audio_presence: Whether to ensure the audio file exists before
                invoking the client.
        """
        if words_per_chunk <= 0:
            message = 'words_per_chunk must be positive'
            raise ValueError(message)

        self._client = transcript_client
        self._raw_audio_dir = raw_audio_dir or RAW_AUDIO_DIR
        self._words_per_chunk = words_per_chunk
        self._enforce_audio_presence = enforce_audio_presence

    async def stream_transcript(self, meeting_id: str) -> AsyncGenerator[dict[str, Any], None]:
        """Yield transcript chunks for the provided meeting identifier.

        Args:
            meeting_id: Identifier of the meeting whose transcript should be streamed.

        Yields:
            Dictionaries with chunk metadata and text content.
        """
        audio_path = self._raw_audio_dir / f'{meeting_id}.wav'
        if self._enforce_audio_presence:
            audio_path = self._resolve_audio_path(meeting_id)
        payload = await self._client.run(audio_path)

        for index, chunk in enumerate(self._extract_chunks(payload), start=1):
            yield {'index': index, 'text': chunk}

    def ensure_audio_available(self, meeting_id: str) -> None:
        """Validate that raw audio exists for the provided meeting identifier."""
        self._resolve_audio_path(meeting_id)

    def _resolve_audio_path(self, meeting_id: str) -> Path:
        """Return audio file path and ensure it exists."""
        audio_path = self._raw_audio_dir / f'{meeting_id}.wav'
        if not audio_path.is_file():
            raise MeetingNotFoundError(meeting_id)
        return audio_path

    def _extract_chunks(self, payload: dict[str, Any]) -> Iterable[str]:
        """Extract text chunks from transcription payload."""
        segments = payload.get('segments')
        if isinstance(segments, list):
            for segment in segments:
                if not isinstance(segment, dict):
                    continue
                text = segment.get('text')
                if isinstance(text, str):
                    cleaned = text.strip()
                    if cleaned:
                        yield cleaned
            return

        text = payload.get('text')
        if isinstance(text, str):
            cleaned = text.strip()
            if cleaned:
                yield from self._chunk_text(cleaned)

    def _chunk_text(self, text: str) -> Iterable[str]:
        """Split raw text into word-based chunks."""
        words = text.split()
        if not words:
            return

        for start in range(0, len(words), self._words_per_chunk):
            yield ' '.join(words[start : start + self._words_per_chunk])


def resolve_transcribe_fixture_path() -> Path:
    """Determine transcript fixture path for the mock gRPC client."""
    env_path = os.getenv('TRANSCRIBE_FIXTURE_PATH')
    if env_path:
        return Path(env_path)
    return DEFAULT_TRANSCRIBE_FIXTURE


def get_transcript_service(
    client_type: str | None = None,
    gpu_settings: GPUSettings | None = None,
) -> TranscriptService:
    """Return transcript service instance configured with selected gRPC client."""
    fixture_path = resolve_transcribe_fixture_path()
    resolved_type = client_type or os.getenv('GRPC_CLIENT_TYPE', 'mock')
    if resolved_type == 'grpc' and gpu_settings is None:
        gpu_settings = GPUSettings()

    client = create_grpc_client(
        'transcribe',
        fixture_path,
        client_type=client_type,
        gpu_settings=gpu_settings,
    )
    return TranscriptService(cast('TranscriptClientProtocol', client))

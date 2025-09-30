"""Domain-level meeting processing service."""

from __future__ import annotations

import asyncio
import math
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, NotRequired, Protocol, TypedDict

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterable, Iterator
    from pathlib import Path


class TranscribeClientProtocol(Protocol):
    """Protocol describing the transcription client."""

    async def run(self, source: Iterable[bytes]) -> dict[str, Any]:  # pragma: no cover - protocol
        """Return transcription payload for the provided audio source."""


class DiarizeClientProtocol(Protocol):
    """Protocol describing the diarization client."""

    async def run(self, source: Iterable[bytes]) -> dict[str, Any]:  # pragma: no cover - protocol
        """Return diarization payload for the provided audio source."""


class SummarizeClientProtocol(Protocol):
    """Protocol describing the summarization client."""

    async def run(self, transcript: str) -> dict[str, Any]:  # pragma: no cover - protocol
        """Return summary payload for the provided transcript text."""


class MeetingEvent(TypedDict):
    """Structured data describing a single meeting fragment."""

    speaker: str
    text: str
    confidence: float | None
    summary_fragment: str
    start: NotRequired[float | None]
    end: NotRequired[float | None]


@dataclass(slots=True)
class MeetingProcessingResult:
    """Aggregate result of the meeting processing pipeline."""

    events: list[MeetingEvent]
    summary: str


class MeetingProcessingService:
    """Combine transcription, diarization and summarization results."""

    def __init__(
        self,
        transcribe_client: TranscribeClientProtocol,
        diarize_client: DiarizeClientProtocol,
        summarize_client: SummarizeClientProtocol,
    ) -> None:
        """Store dependencies required for meeting processing."""
        self._transcribe_client = transcribe_client
        self._diarize_client = diarize_client
        self._summarize_client = summarize_client

    async def process(self, audio_path: Path) -> MeetingProcessingResult:
        """Execute the processing pipeline for a single meeting.

        Args:
            audio_path: Path to the audio file that should be processed.

        Returns:
            Result containing aggregated events and final summary text.
        """
        transcribe_stream = self._iter_audio_chunks(audio_path)
        diarize_stream = self._iter_audio_chunks(audio_path)

        transcribe_task = asyncio.create_task(self._transcribe_client.run(transcribe_stream))
        diarize_task = asyncio.create_task(self._diarize_client.run(diarize_stream))

        transcribe_payload, diarize_payload = await asyncio.gather(transcribe_task, diarize_task)

        transcript_text = self._build_summary_input(transcribe_payload)
        summary_payload = await self._summarize_client.run(transcript_text)

        diarization_segments = self._normalize_diarization_segments(diarize_payload)
        transcript_segments = self._normalize_transcription_segments(transcribe_payload)

        summary_fragments = self._build_summary_fragments(summary_payload, len(transcript_segments))

        events: list[MeetingEvent] = []
        for index, segment in enumerate(transcript_segments):
            events.append(
                {
                    'speaker': self._resolve_speaker(segment, diarization_segments),
                    'text': segment['text'],
                    'confidence': segment['confidence'],
                    'summary_fragment': summary_fragments[index] if summary_fragments else '',
                    'start': segment['start'],
                    'end': segment['end'],
                }
            )

        summary = self._extract_summary_text(summary_payload, summary_fragments)

        return MeetingProcessingResult(events=events, summary=summary)

    def _iter_audio_chunks(
        self,
        audio_path: Path,
        *,
        chunk_size: int = 64 * 1024,
    ) -> Iterable[bytes]:
        """Yield audio file contents in fixed-size chunks."""

        def generator() -> Iterator[bytes]:
            with audio_path.open('rb') as audio_file:
                while True:
                    chunk = audio_file.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        return generator()

    def _build_summary_input(self, payload: dict[str, Any]) -> str:
        """Return raw transcript text suitable for summarization input."""
        segments = payload.get('segments')
        if isinstance(segments, list):
            texts: list[str] = []
            for segment in segments:
                text = segment.get('text') if isinstance(segment, dict) else None
                if isinstance(text, str):
                    cleaned = text.strip()
                    if cleaned:
                        texts.append(cleaned)
            if texts:
                return ' '.join(texts)

        text = payload.get('text')
        if isinstance(text, str):
            return text.strip()

        return ''

    def _normalize_transcription_segments(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalize transcription payload to a list of segment dictionaries."""
        segments = payload.get('segments')
        normalized: list[dict[str, Any]] = []

        if isinstance(segments, list):
            for segment in segments:
                if not isinstance(segment, dict):
                    continue
                text = segment.get('text')
                if not isinstance(text, str):
                    continue
                cleaned = text.strip()
                if not cleaned:
                    continue
                normalized.append(
                    {
                        'start': self._as_float(segment.get('start')),
                        'end': self._as_float(segment.get('end')),
                        'text': cleaned,
                        'confidence': self._as_float(segment.get('confidence')),
                    }
                )

        if normalized:
            normalized.sort(key=lambda item: (math.inf if item['start'] is None else item['start']))
            return normalized

        text = payload.get('text')
        cleaned_text = text.strip() if isinstance(text, str) else ''
        if cleaned_text:
            return [
                {
                    'start': None,
                    'end': None,
                    'text': cleaned_text,
                    'confidence': self._as_float(payload.get('confidence')),
                }
            ]

        return []

    def _normalize_diarization_segments(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalize diarization payload to a list of segment dictionaries."""
        segments = payload.get('segments')
        normalized: list[dict[str, Any]] = []

        if not isinstance(segments, list):
            return normalized

        for segment in segments:
            if not isinstance(segment, dict):
                continue
            speaker = segment.get('speaker')
            if not isinstance(speaker, str):
                continue
            normalized.append(
                {
                    'start': self._as_float(segment.get('start')),
                    'end': self._as_float(segment.get('end')),
                    'speaker': speaker,
                }
            )

        normalized.sort(key=lambda item: (math.inf if item['start'] is None else item['start']))
        return normalized

    def _build_summary_fragments(self, payload: dict[str, Any], expected_length: int) -> list[str]:
        """Produce per-segment summary fragments."""
        if expected_length == 0:
            return []

        candidates = payload.get('fragments') or payload.get('highlights')
        fragments: list[str] = []

        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, str):
                    cleaned = item.strip()
                    if cleaned:
                        fragments.append(cleaned)

        if not fragments:
            summary_text = payload.get('summary')
            if isinstance(summary_text, str):
                sentences = [
                    sentence.strip()
                    for sentence in re.split(r'(?<=[.!?])\s+', summary_text)
                    if sentence.strip()
                ]
                fragments.extend(sentences)

        if not fragments:
            return [''] * expected_length

        if len(fragments) >= expected_length:
            return fragments[:expected_length]

        return fragments + [''] * (expected_length - len(fragments))

    def _extract_summary_text(self, payload: dict[str, Any], fragments: list[str]) -> str:
        """Extract final summary text from payload and fragments."""
        summary_text = payload.get('summary')
        if isinstance(summary_text, str) and summary_text.strip():
            return summary_text.strip()

        combined = ' '.join(fragment for fragment in fragments if fragment)
        return combined.strip()

    def _resolve_speaker(
        self,
        segment: dict[str, Any],
        diarization_segments: list[dict[str, Any]],
    ) -> str:
        """Match a transcription segment to the most relevant speaker."""
        start = segment.get('start')
        end = segment.get('end')

        if start is None and end is None:
            return diarization_segments[0]['speaker'] if diarization_segments else 'Unknown'

        for diar_segment in diarization_segments:
            diar_start = diar_segment['start']
            diar_end = diar_segment['end']

            if diar_start is None and diar_end is None:
                return diar_segment['speaker']

            if self._segments_overlap(start, end, diar_start, diar_end):
                return diar_segment['speaker']

        return 'Unknown'

    @staticmethod
    def _segments_overlap(
        start: float | None,
        end: float | None,
        diar_start: float | None,
        diar_end: float | None,
    ) -> bool:
        """Return ``True`` when the provided intervals overlap."""
        norm_start = float('-inf') if start is None else start
        norm_end = float('inf') if end is None else end
        norm_diar_start = float('-inf') if diar_start is None else diar_start
        norm_diar_end = float('inf') if diar_end is None else diar_end

        if norm_start >= norm_diar_end:
            return False

        return norm_end > norm_diar_start

    @staticmethod
    def _as_float(value: float | str | None) -> float | None:
        """Convert arbitrary value to float when possible."""
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None


__all__ = [
    'DiarizeClientProtocol',
    'MeetingEvent',
    'MeetingProcessingResult',
    'MeetingProcessingService',
    'SummarizeClientProtocol',
    'TranscribeClientProtocol',
]

"""Tests for pipeline service orchestration."""

from __future__ import annotations

import pytest

from app.services.pipeline import get_pipeline_service


@pytest.mark.asyncio
async def test_pipeline_service_streams_mock_clients() -> None:
    """Pipeline produces transcript, diarization and summary events."""
    service = get_pipeline_service(client_type='mock')

    events = [
        (event['type'], event['payload']) async for event in service.stream_pipeline('meeting-id')
    ]

    event_types = [etype for etype, _ in events]
    assert 'transcribe' in event_types
    assert 'diarize' in event_types
    assert 'summarize' in event_types
    summary_payload = next(payload for etype, payload in events if etype == 'summarize')
    assert summary_payload['summary'] == 'This is a summary.'

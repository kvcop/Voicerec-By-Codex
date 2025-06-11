"""Tests for mock gRPC clients."""

from pathlib import Path

import pytest

from app.grpc_client import (
    MockDiarizeClient,
    MockSummarizeClient,
    MockTranscribeClient,
)

FIXTURES = Path(__file__).parent / 'fixtures'


@pytest.mark.asyncio
async def test_transcribe_client() -> None:
    """Client returns transcript from fixture."""
    client = MockTranscribeClient(FIXTURES / 'transcribe.json')
    result = await client.run(Path('dummy.wav'))
    assert result == {'text': 'hello world'}


@pytest.mark.asyncio
async def test_diarize_client() -> None:
    """Client returns diarization segments from fixture."""
    client = MockDiarizeClient(FIXTURES / 'diarize.json')
    result = await client.run(Path('dummy.wav'))
    expected_segments = 2
    assert result['segments'][0]['speaker'] == 'A'
    assert len(result['segments']) == expected_segments


@pytest.mark.asyncio
async def test_summarize_client() -> None:
    """Client returns summary from fixture."""
    client = MockSummarizeClient(FIXTURES / 'summarize.json')
    result = await client.run('some text')
    assert result == {'summary': 'This is a summary.'}

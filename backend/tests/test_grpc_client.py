"""Tests for mock gRPC clients."""

from pathlib import Path

import pytest

from app.grpc_client import (
    MockDiarizeClient,
    MockSummarizeClient,
    MockTranscribeClient,
    create_grpc_client,
)

FIXTURES = Path(__file__).parent / 'fixtures'


@pytest.mark.asyncio
async def test_transcribe_client() -> None:
    """Client returns transcript from fixture."""
    client = create_grpc_client('transcribe', FIXTURES / 'transcribe.json', 'mock')
    assert isinstance(client, MockTranscribeClient)
    result = await client.run(Path('dummy.wav'))
    assert result == {'text': 'hello world'}
    chunks = [chunk async for chunk in client.stream_run(Path('dummy.wav'))]
    assert chunks == [{'text': 'hello world'}]


@pytest.mark.asyncio
async def test_diarize_client() -> None:
    """Client returns diarization segments from fixture."""
    client = create_grpc_client('diarize', FIXTURES / 'diarize.json', 'mock')
    assert isinstance(client, MockDiarizeClient)
    result = await client.run(Path('dummy.wav'))
    expected_segments = 2
    assert result['segments'][0]['speaker'] == 'A'
    assert len(result['segments']) == expected_segments
    streamed = [chunk async for chunk in client.stream_run(Path('dummy.wav'))]
    assert len(streamed) == expected_segments
    assert streamed[0]['speaker'] == 'A'


@pytest.mark.asyncio
async def test_summarize_client() -> None:
    """Client returns summary from fixture."""
    client = create_grpc_client('summarize', FIXTURES / 'summarize.json', 'mock')
    assert isinstance(client, MockSummarizeClient)
    result = await client.run('some text')
    assert result == {'summary': 'This is a summary.'}
    streamed = [chunk async for chunk in client.stream_run('some text')]
    assert streamed == [{'summary': 'This is a summary.'}]


@pytest.mark.asyncio
async def test_factory_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Factory selects client type from environment variable."""
    monkeypatch.setenv('GRPC_CLIENT_TYPE', 'mock')
    client = create_grpc_client('transcribe', FIXTURES / 'transcribe.json')
    assert isinstance(client, MockTranscribeClient)

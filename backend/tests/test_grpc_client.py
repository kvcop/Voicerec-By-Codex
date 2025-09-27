"""Tests for mock gRPC clients."""

from collections.abc import Iterable, Iterator
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

    tracking = _TrackingIterable([b'hello', b' ', b'world'])
    result = await client.run(tracking)
    assert result == {'text': 'hello world'}
    assert tracking.consumed_chunks == [b'hello', b' ', b'world']


@pytest.mark.asyncio
async def test_diarize_client() -> None:
    """Client returns diarization segments from fixture."""
    client = create_grpc_client('diarize', FIXTURES / 'diarize.json', 'mock')
    assert isinstance(client, MockDiarizeClient)

    tracking = _TrackingIterable([b'audio'])
    result = await client.run(tracking)
    expected_segments = 2
    assert result['segments'][0]['speaker'] == 'A'
    assert len(result['segments']) == expected_segments
    assert tracking.consumed_chunks == [b'audio']


@pytest.mark.asyncio
async def test_summarize_client() -> None:
    """Client returns summary from fixture."""
    client = create_grpc_client('summarize', FIXTURES / 'summarize.json', 'mock')
    assert isinstance(client, MockSummarizeClient)
    result = await client.run('some text')
    assert result == {'summary': 'This is a summary.'}


@pytest.mark.asyncio
async def test_factory_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Factory selects client type from environment variable."""
    monkeypatch.setenv('GRPC_CLIENT_TYPE', 'mock')
    client = create_grpc_client('transcribe', FIXTURES / 'transcribe.json')
    assert isinstance(client, MockTranscribeClient)


class _TrackingIterable:
    """Helper iterable that records consumed chunks."""

    def __init__(self, chunks: Iterable[bytes]) -> None:
        self._chunks = list(chunks)
        self.consumed_chunks: list[bytes] = []

    def __iter__(self) -> Iterator[bytes]:
        for chunk in self._chunks:
            self.consumed_chunks.append(chunk)
            yield chunk

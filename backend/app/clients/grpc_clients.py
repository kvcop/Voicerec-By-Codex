"""Async gRPC client wrappers for GPU services."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import grpc  # type: ignore[import-untyped]  # noqa: TC002
from google.protobuf.json_format import MessageToDict  # type: ignore[import-untyped]

from app.clients import (
    diarize_pb2 as _diarize_pb2,
)
from app.clients import (
    diarize_pb2_grpc,
    summarize_pb2_grpc,
    transcribe_pb2_grpc,
)
from app.clients import (
    summarize_pb2 as _summarize_pb2,
)
from app.clients import (
    transcribe_pb2 as _transcribe_pb2,
)

diarize_pb2 = cast('Any', _diarize_pb2)
summarize_pb2 = cast('Any', _summarize_pb2)
transcribe_pb2 = cast('Any', _transcribe_pb2)

if TYPE_CHECKING:  # pragma: no cover - imports for typing only
    from collections.abc import AsyncIterator
    from pathlib import Path

    from google.protobuf.message import Message  # type: ignore[import-untyped]


def _message_to_dict(message: Message) -> dict[str, Any]:
    """Convert protobuf message into plain dictionary."""
    return cast('dict[str, Any]', MessageToDict(message, preserving_proto_field_name=True))


class _BaseGrpcClient:
    """Base gRPC client with channel lifecycle management."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        self._channel = channel

    async def close(self) -> None:
        """Close the underlying gRPC channel."""
        await self._channel.close()


class TranscribeGrpcClient(_BaseGrpcClient):
    """Call the remote Transcribe service and stream transcript fragments."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        super().__init__(channel)
        self._stub = transcribe_pb2_grpc.TranscribeStub(channel)

    async def run(self, source: Path) -> dict[str, Any]:
        """Fetch the entire transcript payload for the provided audio source."""
        request = transcribe_pb2.AudioRequest(path=str(source))
        response = await self._stub.Run(request)
        return _message_to_dict(response)

    async def stream_run(self, source: Path) -> AsyncIterator[dict[str, Any]]:
        """Yield transcript fragments for streaming use cases."""
        payload = await self.run(source)
        segments = payload.get('segments')
        if isinstance(segments, list):
            for segment in segments:
                if isinstance(segment, dict):
                    yield {'segment': segment}
            return

        text = payload.get('text')
        if isinstance(text, str):
            yield {'text': text}


class DiarizeGrpcClient(_BaseGrpcClient):
    """Call the remote Diarize service and stream segments."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        super().__init__(channel)
        self._stub = diarize_pb2_grpc.DiarizeStub(channel)

    async def run(self, source: Path) -> dict[str, Any]:
        """Fetch diarization segments for the provided audio source."""
        request = diarize_pb2.AudioRequest(path=str(source))
        response = await self._stub.Run(request)
        return _message_to_dict(response)

    async def stream_run(self, source: Path) -> AsyncIterator[dict[str, Any]]:
        """Yield diarization segments one by one."""
        payload = await self.run(source)
        segments = payload.get('segments')
        if isinstance(segments, list):
            for segment in segments:
                if isinstance(segment, dict):
                    yield segment


class SummarizeGrpcClient(_BaseGrpcClient):
    """Call the remote Summarize service and stream summary text."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        super().__init__(channel)
        self._stub = summarize_pb2_grpc.SummarizeStub(channel)

    async def run(self, text: str) -> dict[str, Any]:
        """Fetch summary for the provided transcript text."""
        request = summarize_pb2.TextRequest(text=text)
        response = await self._stub.Run(request)
        return _message_to_dict(response)

    async def stream_run(self, text: str) -> AsyncIterator[dict[str, Any]]:
        """Yield summary chunks. Currently returns a single response."""
        payload = await self.run(text)
        summary_text = payload.get('text')
        if isinstance(summary_text, str):
            yield {'text': summary_text}
        else:
            yield payload


__all__ = [
    'DiarizeGrpcClient',
    'SummarizeGrpcClient',
    'TranscribeGrpcClient',
]

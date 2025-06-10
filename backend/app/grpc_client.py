"""Asynchronous mock gRPC clients."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from pathlib import Path


class MockTranscribeClient:
    """Return transcript fixture instead of real gRPC call."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path

    async def run(self, _: Path) -> dict[str, Any]:
        """Return transcript data from fixture."""
        return json.loads(self._fixture_path.read_text(encoding='utf-8'))


class MockDiarizeClient:
    """Return diarization fixture instead of real gRPC call."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path

    async def run(self, _: Path) -> dict[str, Any]:
        """Return diarization data from fixture."""
        return json.loads(self._fixture_path.read_text(encoding='utf-8'))


class MockSummarizeClient:
    """Return summary fixture instead of real gRPC call."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path

    async def run(self, _: str) -> dict[str, Any]:
        """Return summary data from fixture."""
        return json.loads(self._fixture_path.read_text(encoding='utf-8'))

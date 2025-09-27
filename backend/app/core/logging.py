"""Logging configuration utilities."""

from __future__ import annotations

import os
import sys
from typing import Final

from loguru import logger

_CONFIG_STATE: Final[dict[str, bool]] = {'configured': False}


def configure_logging() -> None:
    """Configure the global Loguru logger for structured output."""
    if _CONFIG_STATE['configured']:
        return

    logger.remove()
    logger.add(
        sys.stdout,
        level=os.getenv('LOG_LEVEL', 'INFO'),
        enqueue=True,
        backtrace=False,
        diagnose=False,
        serialize=True,
    )

    _CONFIG_STATE['configured'] = True


__all__ = ['configure_logging', 'logger']

"""
Public exceptions raised throughout WumpiWave.

This package contains the exception hierarchy shared by media queries,
providers, resolvers, playback queues, voice backends, and media players.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .base import WumpiWaveError
from .query import (
    InvalidQueryError,
    MediaNotFoundError,
    QueryError,
    UnsupportedQueryError,
)

__all__: tuple[str, ...] = (
    "InvalidQueryError",
    "MediaNotFoundError",
    "QueryError",
    "UnsupportedQueryError",
    "WumpiWaveError",
)
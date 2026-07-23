"""
Public data models used throughout WumpiWave.

This package contains the source-independent models shared by providers,
resolvers, queues, players, events, and playback backends. External service
objects from Discord, YouTube, Spotify, or other integrations must not be
stored directly inside these models.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .enums import (
    LoopMode,
    MediaSource,
    MediaType,
    PlayerState,
    QueryType,
    TrackEndReason,
)
from .media import (
    MediaArtist,
    MediaCollection,
    MediaImage,
    MediaStatistics,
    MediaTrack,
)

__all__: tuple[str, ...] = (
    "LoopMode",
    "MediaArtist",
    "MediaCollection",
    "MediaImage",
    "MediaSource",
    "MediaStatistics",
    "MediaTrack",
    "MediaType",
    "PlayerState",
    "QueryType",
    "TrackEndReason",
)
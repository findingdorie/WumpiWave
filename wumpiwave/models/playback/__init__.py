"""
Public playback models used throughout WumpiWave.

This package contains source-independent models for playable audio sources,
queue entries, playback events, and other data shared by resolvers, players,
queues, and playback backends.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .queue import QueueEntry
from .source import PlayableSource

__all__: tuple[str, ...] = (
    "PlayableSource",
    "QueueEntry",
)
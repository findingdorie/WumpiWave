"""Playback management components available in WumpiWave.

This package contains queue management, media player coordination, player
registration, playback state, and lifecycle components.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .player import WumpiWavePlayer
from .queue import PlaybackQueue
from .registry import PlayerRegistry

__all__: tuple[str, ...] = (
    "PlaybackQueue",
    "PlayerRegistry",
    "WumpiWavePlayer",
)
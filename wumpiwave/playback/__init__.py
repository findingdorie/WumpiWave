"""Playback management components available in WumpiWave.

This package contains queue management, player coordination, playback state,
and lifecycle components used by WumpiWave media players.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .queue import PlaybackQueue

__all__: tuple[str, ...] = ("PlaybackQueue",)
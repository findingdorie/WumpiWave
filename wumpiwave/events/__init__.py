"""Playback event utilities available in WumpiWave.

This package contains asynchronous event dispatching components used to
register listeners and deliver player lifecycle, state, queue, and track
events.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .dispatcher import PlaybackEventDispatcher

__all__: tuple[str, ...] = ("PlaybackEventDispatcher",)
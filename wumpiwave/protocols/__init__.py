"""Public protocol definitions used throughout WumpiWave.

This package contains structural interfaces for metadata providers, stream
resolvers, playback backends, event dispatchers, and media players.

Protocols allow custom implementations to integrate with WumpiWave without
inheriting from concrete base classes.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .backend import PlaybackBackend, PlaybackCompletionCallback
from .dispatcher import (
    EventDispatcher,
    EventListener,
    EventListenerDecorator,
)
from .player import MediaPlayer
from .provider import MediaProvider
from .resolver import StreamResolver

__all__: tuple[str, ...] = (
    "EventDispatcher",
    "EventListener",
    "EventListenerDecorator",
    "MediaPlayer",
    "MediaProvider",
    "PlaybackBackend",
    "PlaybackCompletionCallback",
    "StreamResolver"
)
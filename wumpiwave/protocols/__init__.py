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

from .provider import MediaProvider

__all__: tuple[str, ...] = ("MediaProvider",)
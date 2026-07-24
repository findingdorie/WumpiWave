"""Public metadata providers available in WumpiWave.

This package contains provider implementations responsible for retrieving and
normalizing media metadata from external services such as YouTube and Spotify.

Providers expose only WumpiWave data models and must not leak service-specific
objects through their public interfaces.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .base import BaseMediaProvider
from .youtube import YouTubeClient, YouTubeParser, YouTubeProvider

__all__: tuple[str, ...] = (
    "BaseMediaProvider",
    "YouTubeClient",
    "YouTubeParser",
    "YouTubeProvider",
)
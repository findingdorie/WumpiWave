"""YouTube metadata provider components used by WumpiWave.

This package contains the HTTP client, response models, parsers, and provider
implementation required to retrieve and normalize YouTube media metadata.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .client import YouTubeClient, YouTubeSearchResource
from .parser import YouTubeParser
from .provider import YouTubeProvider

__all__: tuple[str, ...] = (
    "YouTubeClient",
    "YouTubeParser",
    "YouTubeProvider",
    "YouTubeSearchResource",
)
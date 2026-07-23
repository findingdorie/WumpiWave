"""
Public media metadata models used throughout WumpiWave.

This package contains source-independent representations of artists, images,
statistics, tracks, and media collections. Provider-specific objects from
YouTube, Spotify, or other services must not be exposed through these models.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .artist import MediaArtist
from .image import MediaImage
from .statistics import MediaStatistics
from .track import MediaTrack

__all__: tuple[str, ...] = (
    "MediaArtist",
    "MediaImage",
    "MediaStatistics",
    "MediaTrack",
)
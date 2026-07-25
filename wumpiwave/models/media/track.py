"""Track data models used throughout WumpiWave.

This module provides the source-independent representation of individual
media tracks returned by supported metadata providers.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

from ..enums import MediaSource
from .artist import MediaArtist
from .image import MediaImage
from .statistics import MediaStatistics

@dataclass(frozen=True, slots=True)
class MediaTrack:
    """Represents an individual media track from a supported provider.

    A media track contains normalized metadata that can be shared between
    providers, resolvers, queues, and players without exposing objects from
    YouTube, Spotify, Discord, or other external integrations.

    Temporary audio stream URLs are intentionally excluded because they may
    expire and belong to a separately resolved playable source.

    Attributes:
        - identifier:
            The unique provider-specific identifier of the track.
        - source:
            The platform or source from which the track originates.
        - title:
            The public title of the track.
        - url:
            The permanent public URL associated with the track.
        - duration:
            The total duration of the track in seconds, when available.
        - artists:
            The artists, creators, or channels associated with the track.
        - thumbnails:
            The available thumbnails or artwork associated with the track.
        - statistics:
            The publicly available statistics associated with the track.
        - description:
            The public description of the track, when available.
        - album_name:
            The name of the album containing the track, when available.
        - release_date:
            The provider-supplied release date in ISO 8601 format, when
            available.
        - is_live:
            Whether the track represents a livestream.
        - is_explicit:
            Whether the provider marks the track as explicit.

    Methods:
        __post_init__:
            Validates the required track metadata and optional duration.
    """

    identifier: str
    source: MediaSource
    title: str
    url: str
    duration: float | None = None
    artists: tuple[MediaArtist, ...] = ()
    thumbnails: tuple[MediaImage, ...] = ()
    statistics: MediaStatistics = field(default_factory=MediaStatistics)
    description: str | None = None
    album_name: str | None = None
    release_date: str | None = None
    is_live: bool = False
    is_explicit: bool = False

    def __post_init__(self) -> None:
        """Validate the media track metadata.

        Raises:
            ValueError:
                The identifier, title, or URL is empty, or the supplied
                duration is negative or not finite.
        """
        if not self.identifier.strip():
            raise ValueError("The track identifier cannot be empty.")

        if not self.title.strip():
            raise ValueError("The track title cannot be empty.")

        if not self.url.strip():
            raise ValueError("The track URL cannot be empty.")

        if self.duration is not None:
            if not isfinite(self.duration):
                raise ValueError("The track duration must be finite.")

            if self.duration < 0.0:
                raise ValueError("The track duration cannot be negative.")

__all__: tuple[str, ...] = ("MediaTrack",)

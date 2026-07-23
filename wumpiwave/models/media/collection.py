"""Media collection models used throughout WumpiWave.

This module provides the source-independent representation of playlists,
albums, and other ordered collections of media tracks.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from dataclasses import dataclass

from ..enums import MediaSource, MediaType
from .artist import MediaArtist
from .image import MediaImage
from .track import MediaTrack


@dataclass(frozen=True, slots=True)
class MediaCollection:
    """Represents an ordered collection of media tracks.

    A media collection contains normalized metadata for playlists and albums
    without exposing provider-specific objects from YouTube, Spotify, or other
    external integrations.

    Attributes:
        - identifier:
            The unique provider-specific identifier of the collection.
        - source:
            The platform or source from which the collection originates.
        - media_type:
            The type of collection, such as a playlist or album.
        - title:
            The public title of the collection.
        - url:
            The permanent public URL associated with the collection.
        - tracks:
            The ordered tracks contained in the collection.
        - thumbnails:
            The available artwork or thumbnails associated with the collection.
        - author:
            The artist, creator, channel, or owner of the collection.
        - description:
            The public description of the collection, when available.

    Methods:
        __post_init__:
            Validates the required collection metadata and media type.
    """

    identifier: str
    source: MediaSource
    media_type: MediaType
    title: str
    url: str
    tracks: tuple[MediaTrack, ...] = ()
    thumbnails: tuple[MediaImage, ...] = ()
    author: MediaArtist | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        """Validate the media collection metadata.

        Raises:
            ValueError:
                The identifier, title, or URL is empty, or the supplied media
                type does not represent a collection.
        """
        if not self.identifier.strip():
            raise ValueError("The collection identifier cannot be empty.")

        if not self.title.strip():
            raise ValueError("The collection title cannot be empty.")

        if not self.url.strip():
            raise ValueError("The collection URL cannot be empty.")

        if self.media_type is MediaType.TRACK:
            raise ValueError("A media collection cannot use the track media type.")


__all__: tuple[str, ...] = ("MediaCollection",)

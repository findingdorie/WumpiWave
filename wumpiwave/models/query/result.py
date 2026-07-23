"""
Query result models used throughout WumpiWave.

This module provides the source-independent representation of media metadata
returned by providers after processing a media query.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from ..enums import MediaSource
from ..media import MediaCollection, MediaTrack
from dataclasses import dataclass
from .query import MediaQuery

@dataclass(frozen=True, slots=True)
class MediaResult:
    """
    Represents the normalized result of a processed media query.

    A media result contains the original query, the provider source, returned
    tracks, and an optional playlist or album. When a collection is supplied
    without an explicit track tuple, its tracks are automatically exposed
    through the result.

    Attributes:
        - query:
            The normalized media query used to produce the result.
        - source:
            The media source that processed the query.
        - tracks:
            The ordered media tracks returned by the provider.
        - collection:
            The playlist, album, or other media collection returned by the
            provider, when available.

    Methods:
        __post_init__:
            Normalizes the result tracks using the supplied collection.
        first:
            Returns the first available media track.
        is_empty:
            Indicates whether the result contains no media tracks.
        is_collection:
            Indicates whether the result contains a media collection.
        total_tracks:
            Returns the number of media tracks in the result.
        __bool__:
            Indicates whether the result contains at least one media track.
        __len__:
            Returns the number of media tracks in the result.
    """

    query: MediaQuery
    source: MediaSource
    tracks: tuple[MediaTrack, ...] = ()
    collection: MediaCollection | None = None

    def __post_init__(self) -> None:
        """
        Normalize the media tracks stored in the result.

        Tracks from the supplied collection are used automatically when the
        result does not contain an explicit track tuple.
        """

        if not self.tracks and self.collection is not None:
            object.__setattr__(self, "tracks", self.collection.tracks)

    @property
    def first(self) -> MediaTrack | None:
        """
        Return the first media track in the result.

        Returns:
            The first available media track, or ``None`` when the result is
            empty.
        """

        return self.tracks[0] if self.tracks else None

    @property
    def is_empty(self) -> bool:
        """
        Return whether the result contains no media tracks.

        Returns:
            ``True`` when no tracks are available, otherwise ``False``.
        """

        return not self.tracks

    @property
    def is_collection(self) -> bool:
        """
        Return whether the result contains a media collection.

        Returns:
            ``True`` when a collection is available, otherwise ``False``.
        """

        return self.collection is not None

    @property
    def total_tracks(self) -> int:
        """
        Return the number of media tracks in the result.

        Returns:
            The total number of available media tracks.
        """

        return len(self.tracks)

    def __bool__(self) -> bool:
        """
        Return whether the result contains at least one media track.

        Returns:
            ``True`` when tracks are available, otherwise ``False``.
        """

        return bool(self.tracks)

    def __len__(self) -> int:
        """
        Return the number of media tracks in the result.

        Returns:
            The total number of available media tracks.
        """

        return len(self.tracks)

__all__: tuple[str, ...] = (
    "MediaResult",
)
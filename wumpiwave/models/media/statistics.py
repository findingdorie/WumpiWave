"""Media statistics models used throughout WumpiWave.

This module provides a source-independent representation of statistics
associated with tracks, videos, playlists, and other media resources.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MediaStatistics:
    """Represents publicly available statistics for a media resource.

    All values are optional because supported providers expose different
    statistics. A missing value represents unavailable information and must
    not be interpreted as zero.

    Attributes:
        - view_count:
            The total number of recorded views, when available.
        - like_count:
            The total number of recorded likes, when available.
        - comment_count:
            The total number of recorded comments, when available.
        - popularity_score:
            The provider-defined popularity score, when available.

    Methods:
        None
    """

    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    popularity_score: int | None = None


__all__: tuple[str, ...] = ("MediaStatistics",)

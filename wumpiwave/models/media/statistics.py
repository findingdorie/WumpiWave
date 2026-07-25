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
        __post_init__:
            Validate the media statistics.
    """

    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    popularity_score: int | None = None

    def __post_init__(self) -> None:
        """Validate the media statistics.

        Raises:
            ValueError:
                A counter is negative or the popularity score is outside
                the supported range.
        """

        counters: tuple[tuple[str, int | None], ...] = (
            ("view count", self.view_count),
            ("like count", self.like_count),
            ("comment count", self.comment_count)
        )

        for name, value in counters:
            if value is not None and value < 0:
                raise ValueError(f"The media statistics {name} cannot be negative.")

        if (
                self.popularity_score is not None
                and not 0 <= self.popularity_score <= 100
        ):
            raise ValueError(
                "The media statistics popularity score must be between "
                "zero and one hundred."
            )

__all__: tuple[str, ...] = ("MediaStatistics",)
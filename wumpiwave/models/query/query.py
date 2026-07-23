"""
Query data models used throughout WumpiWave.

This module provides the source-independent representation of media queries
submitted to metadata providers and query routers.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from ..enums import MediaSource, QueryType
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class MediaQuery:
    """
    Represents a normalized query for retrieving media metadata.

    A media query contains the submitted search value or URL together with
    optional provider preferences and loading options. Query routers use this
    model to select a compatible metadata provider.

    Attributes:
        - value:
            The search text or media URL submitted by the user.
        - query_type:
            The detected or explicitly supplied format of the query.
        - source:
            The preferred media source, when a specific provider is requested.
        - limit:
            The maximum number of media tracks returned by a provider.
        - include_statistics:
            Whether providers should request additional media statistics.
        - include_collections:
            Whether playlists, albums, and other collections may be returned.

    Methods:
        __post_init__:
            Normalizes and validates the submitted query data.
    """

    value: str
    query_type: QueryType
    source: MediaSource | None = None
    limit: int = 25
    include_statistics: bool = True
    include_collections: bool = True

    def __post_init__(self) -> None:
        """
        Normalize and validate the media query.

        Raises:
            ValueError:
                The query value is empty or the result limit is not positive.
        """

        normalized_value: str = self.value.strip()

        if not normalized_value:
            raise ValueError("The query value cannot be empty.")

        if self.limit <= 0:
            raise ValueError("The query result limit must be greater than zero.")

        object.__setattr__(self, "value", normalized_value)

__all__: tuple[str, ...] = (
    "MediaQuery",
)
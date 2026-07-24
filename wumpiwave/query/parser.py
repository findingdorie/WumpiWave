"""Media query parsing utilities used throughout WumpiWave.

This module converts raw URLs and search values into normalized media query
models without performing network requests.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from ..exceptions import InvalidQueryError
from ..models import MediaQuery, MediaSource, QueryType
from .matcher import QueryMatcher


class QueryParser:
    """Parse raw query values into normalized media queries.

    The parser trims submitted values, determines whether they represent URLs
    or search text, detects supported media sources, and validates explicitly
    requested source preferences.

    Attributes:
        None

    Methods:
        parse:
            Convert a raw query value into a normalized media query.
        detect_query_type:
            Determine whether a value represents a URL or search query.
        _resolve_source:
            Resolve and validate the source associated with a query.
    """

    __slots__ = ()

    @classmethod
    def parse(
            cls,
            query_value: str,
            *,
            preferred_source: MediaSource | None = None,
            result_limit: int = 25,
            include_statistics: bool = True,
            include_collections: bool = True
    ) -> MediaQuery:
        """Convert a raw value into a normalized media query.

        Args:
            query_value:
                The URL or search text submitted by the caller.
            preferred_source:
                The media source that should process the query, when specified.
            result_limit:
                The maximum number of tracks that a provider may return.
            include_statistics:
                Whether providers should request additional media statistics.
            include_collections:
                Whether providers may return playlists, albums, or other
                collections.

        Returns:
            A normalized media query containing the detected query type and
            resolved media source.

        Raises:
            InvalidQueryError:
                The query value is empty, the result limit is invalid, or the
                preferred source conflicts with the detected URL source.
        """

        normalized_query_value = query_value.strip()

        if not normalized_query_value:
            raise InvalidQueryError(
                query_value=query_value,
                reason="The query value cannot be empty."
            )

        if result_limit <= 0:
            raise InvalidQueryError(
                query_value=normalized_query_value,
                reason="The result limit must be greater than zero."
            )

        query_type: QueryType = cls.detect_query_type(normalized_query_value)
        resolved_source: MediaSource | None = cls._resolve_source(
            query_value=normalized_query_value,
            query_type=query_type,
            preferred_source=preferred_source
        )

        return MediaQuery(
            value=normalized_query_value,
            query_type=query_type,
            source=resolved_source,
            limit=result_limit,
            include_statistics=include_statistics,
            include_collections=include_collections
        )

    @staticmethod
    def detect_query_type(query_value: str) -> QueryType:
        """Determine whether a value represents a URL or search query.

        Args:
            query_value:
                The normalized query value to inspect.

        Returns:
            ``QueryType.URL`` for valid HTTP or HTTPS URLs, otherwise
            ``QueryType.SEARCH``.
        """

        if QueryMatcher.is_url(query_value):
            return QueryType.URL

        return QueryType.SEARCH

    @staticmethod
    def _resolve_source(*, query_value: str, query_type: QueryType, preferred_source: MediaSource | None = None) -> MediaSource | None:
        """Resolve and validate the source associated with a query.

        Args:
            query_value:
                The normalized query value being parsed.
            query_type:
                The detected format of the query.
            preferred_source:
                The explicitly requested media source, when available.

        Returns:
            The detected URL source or preferred search source.

        Raises:
            InvalidQueryError:
                The preferred source conflicts with the detected URL source.
        """

        if query_type is QueryType.SEARCH:
            return preferred_source

        detected_source: MediaSource | None = QueryMatcher.detect_source(query_value)

        if detected_source is None:
            return preferred_source

        if (
            preferred_source is not None
            and preferred_source is not MediaSource.UNKNOWN
            and preferred_source is not detected_source
        ):
            raise InvalidQueryError(
                query_value=query_value,
                reason=f"The URL belongs to source {detected_source.value!r}, not {preferred_source.value!r}."
            )

        return detected_source

__al__: tuple[str, ...] = ("QueryParser",)
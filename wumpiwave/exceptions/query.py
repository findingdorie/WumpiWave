"""Query exceptions raised throughout WumpiWave.

This module defines errors related to invalid, unsupported, or unsuccessful
media queries.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .base import WumpiWaveError


class QueryError(WumpiWaveError):
    """Represents the base exception for media query errors.

    Attributes:
        None

    Methods:
        None
    """

    __slots__ = ()


class InvalidQueryError(QueryError):
    """Represents a media query containing invalid input.

    Attributes:
        - query_value:
            The invalid query value supplied by the caller.
        - reason:
            The reason why the query value is considered invalid.

    Methods:
        __init__.py:
            Initializes the exception with the invalid query and reason.
    """

    __slots__ = ("query_value", "reason")

    query_value: str
    reason: str

    def __init__(self, query_value: str, reason: str) -> None:
        """Initialize an invalid query error.

        Args:
            query_value:
                The invalid query value supplied by the caller.
            reason:
                A clear description of why the query is invalid.
        """
        self.query_value = query_value
        self.reason = reason
        super().__init__(f"Invalid media query {query_value!r}: {reason}")


class UnsupportedQueryError(QueryError):
    """Represents a media query unsupported by every registered provider.

    Attributes:
        - query_value:
            The unsupported URL or search value.

    Methods:
        __init__.py:
            Initializes the exception with the unsupported query value.
    """

    __slots__ = ("query_value",)

    query_value: str

    def __init__(self, query_value: str) -> None:
        """Initialize an unsupported query error.

        Args:
            query_value:
                The URL or search value unsupported by registered providers.
        """
        self.query_value = query_value
        super().__init__(
            f"No registered provider supports the media query {query_value!r}."
        )


class MediaNotFoundError(QueryError):
    """Represents a media query that produced no matching results.

    Attributes:
        - query_value:
            The URL or search value that produced no media result.

    Methods:
        __init__.py:
            Initializes the exception with the unsuccessful query value.
    """

    __slots__ = ("query_value",)

    query_value: str

    def __init__(self, query_value: str) -> None:
        """Initialize a media-not-found error.

        Args:
            query_value:
                The URL or search value that produced no matching media.
        """
        self.query_value = query_value
        super().__init__(f"No media was found for the query {query_value!r}.")

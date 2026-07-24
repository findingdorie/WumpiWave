"""Media query routing utilities used throughout WumpiWave.

This module selects compatible metadata providers for normalized media queries
and optionally executes queries through the selected provider.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Iterable

from ..exceptions import UnsupportedQueryError
from ..models import MediaQuery, MediaResult, MediaSource
from ..protocols import MediaProvider


class QueryRouter:
    """Route normalized media queries to compatible metadata providers.

    The router evaluates providers in their supplied order. A provider must
    match the preferred query source, when one is specified, and report support
    for the normalized query before it can be selected.

    Attributes:
        None

    Methods:
        find_providers:
            Return every provider compatible with a media query.
        select_provider:
            Return the first provider compatible with a media query.
        route:
            Execute a media query through the first compatible provider.
        _matches_source:
            Determine whether a provider matches the query source preference.
    """

    __slots__ = ()

    @classmethod
    def find_providers(cls, query: MediaQuery, providers: Iterable[MediaProvider]) -> tuple[MediaProvider, ...]:
        """Return every provider compatible with a media query.

        Providers retain their original iteration order. Providers whose media
        source conflicts with the query source are ignored before their support
        checks are performed.

        Args:
            query:
                The normalized media query to evaluate.
            providers:
                The metadata providers available for query processing.

        Returns:
            Every compatible provider in registration order.
        """

        return tuple(
            provider
            for provider in providers
            if cls._matches_source(query=query, provider=provider)
            and provider.supports(query)
        )

    @classmethod
    def select_provider(cls, query: MediaQuery, providers: Iterable[MediaProvider]) -> MediaProvider:
        """Return the first provider compatible with a media query.

        Args:
            query:
                The normalized media query to route.
            providers:
                The metadata providers available for query processing.

        Returns:
            The first compatible metadata provider.

        Raises:
            UnsupportedQueryError:
                No supplied provider supports the media query.
        """

        for provider in providers:
            if not cls._matches_source(query=query, provider=provider):
                continue

            if provider.supports(query):
                return provider

        raise UnsupportedQueryError(query_value=query.value)

    @classmethod
    async def route(cls, query: MediaQuery, providers: Iterable[MediaProvider]) -> MediaResult:
        """Execute a media query through the first compatible provider.

        Args:
            query:
                The normalized media query to process.
            providers:
                The metadata providers available for query processing.

        Returns:
            The normalized media result returned by the selected provider.

        Raises:
            UnsupportedQueryError:
                No supplied provider supports the media query.
            ProviderError:
                The selected provider could not complete the query.
            QueryError:
                The supplied query is invalid or produced no media.
        """

        provider: MediaProvider = cls.select_provider(
            query=query,
            providers=providers
        )

        return await provider.query(query)

    @classmethod
    def _matches_source(cls, query: MediaQuery, provider: MediaProvider) -> bool:
        """Return whether a provider matches the query source preference.

        Queries without a preferred source and queries using
        ``MediaSource.UNKNOWN`` may be processed by any compatible provider.

        Args:
            query:
                The normalized media query being evaluated.
            provider:
                The metadata provider to compare against the query.

        Returns:
            ``True`` when the provider may process the query, otherwise
            ``False``.
        """

        return (
            query.source is None
            or query.source is MediaSource.UNKNOWN
            or provider.source is query.source
        )

__all__: tuple[str, ...] = ("QueryRouter",)
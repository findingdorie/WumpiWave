"""Tests for the WumpiWave media query router."""

from __future__ import annotations

import unittest

from wumpiwave.exceptions import UnsupportedQueryError
from wumpiwave.models import (
    MediaQuery,
    MediaResult,
    MediaSource,
    MediaTrack,
    QueryType,
)
from wumpiwave.query.router import QueryRouter


class StubProvider:
    """Provide a configurable media provider for router tests.

    Attributes:
        name:
            Human-readable provider name.
        source:
            Media source handled by the provider.
        supported:
            Whether the provider supports the supplied query.
        query_calls:
            Queries passed to the provider.
        closed:
            Whether the provider has been closed.

    Methods:
        supports:
            Return whether the provider supports a query.
        query:
            Execute a query and return a predefined result.
        close:
            Mark the provider as closed.
    """

    def __init__(
        self,
        *,
        name: str,
        source: MediaSource,
        supported: bool = True,
    ) -> None:
        """Initialize the configurable test provider."""

        self.name = name
        self.source = source
        self.supported = supported
        self.query_calls: list[MediaQuery] = []
        self.closed = False

    def supports(self, query: MediaQuery) -> bool:
        """Return whether this provider supports the query."""

        return self.supported

    async def query(self, query: MediaQuery) -> MediaResult:
        """Execute a query and record the received query."""

        self.query_calls.append(query)

        return MediaResult(
            query=query,
            source=self.source,
            tracks=(
                MediaTrack(
                    identifier=f"{self.name}-track",
                    source=self.source,
                    title=f"{self.name} track",
                    url=f"https://example.com/{self.name}-track"
                ),
            )
        )

    async def close(self) -> None:
        """Mark the provider as closed."""

        self.closed = True

class QueryRouterTestCase(unittest.IsolatedAsyncioTestCase):
    """Test provider discovery, selection, and query routing."""

    def setUp(self) -> None:
        """Create reusable queries and providers for each test."""

        self.search_query = MediaQuery(
            value="Example track",
            query_type=QueryType.SEARCH,
            source=None
        )
        self.youtube_query = MediaQuery(
            value="https://www.youtube.com/watch?v=example",
            query_type=QueryType.URL,
            source=MediaSource.YOUTUBE
        )
        self.youtube_provider = StubProvider(
            name="youtube",
            source=MediaSource.YOUTUBE
        )
        self.spotify_provider = StubProvider(
            name="spotify",
            source=MediaSource.SPOTIFY
        )
        self.http_provider = StubProvider(
            name="http",
            source=MediaSource.HTTP
        )

    def test_find_providers_returns_supported_providers(self) -> None:
        """Verify that supported providers are returned."""

        providers = QueryRouter.find_providers(
            self.search_query,
            (
                self.youtube_provider,
                self.spotify_provider
            )
        )

        self.assertEqual(
            providers,
            (
                self.youtube_provider,
                self.spotify_provider
            )
        )

    def test_find_providers_preserves_registration_order(self) -> None:
        """Verify that matching providers retain their supplied order."""

        providers = QueryRouter.find_providers(
            self.search_query,
            (
                self.spotify_provider,
                self.youtube_provider,
                self.http_provider
            )
        )

        self.assertEqual(
            providers,
            (
                self.spotify_provider,
                self.youtube_provider,
                self.http_provider
            )
        )

    def test_find_providers_excludes_unsupported_provider(self) -> None:
        """Verify that providers rejecting the query are excluded."""

        unsupported_provider = StubProvider(
            name="unsupported",
            source=MediaSource.YOUTUBE,
            supported=False
        )

        providers = QueryRouter.find_providers(
            self.search_query,
            (
                unsupported_provider,
                self.spotify_provider
            )
        )

        self.assertEqual(providers, (self.spotify_provider,))

    def test_find_providers_filters_by_requested_source(self) -> None:
        """Verify that a specified source excludes other providers."""

        providers = QueryRouter.find_providers(
            self.youtube_query,
            (
                self.spotify_provider,
                self.youtube_provider,
                self.http_provider
            )
        )

        self.assertEqual(providers, (self.youtube_provider,))

    def test_find_providers_returns_empty_tuple_without_match(self) -> None:
        """Verify that no matching providers produce an empty tuple."""

        providers = QueryRouter.find_providers(
            self.youtube_query,
            (
                self.spotify_provider,
                self.http_provider
            )
        )

        self.assertEqual(providers, ())

    def test_select_provider_returns_first_matching_provider(self) -> None:
        """Verify that the first matching provider is selected."""

        selected_provider = QueryRouter.select_provider(
            self.search_query,
            (
                self.spotify_provider,
                self.youtube_provider
            )
        )

        self.assertIs(selected_provider, self.spotify_provider)

    def test_select_provider_rejects_unsupported_query(self) -> None:
        """Verify that missing provider support raises an error."""

        unsupported_provider = StubProvider(
            name="unsupported",
            source=MediaSource.YOUTUBE,
            supported=False
        )

        with self.assertRaises(UnsupportedQueryError):
            QueryRouter.select_provider(
                self.search_query,
                (unsupported_provider,)
            )

    async def test_route_returns_selected_provider_result(self) -> None:
        """Verify that routing returns the selected provider result."""

        result = await QueryRouter.route(
            self.search_query,
            (
                self.youtube_provider,
                self.spotify_provider
            )
        )

        self.assertIs(result.query, self.search_query)
        self.assertIs(result.source, MediaSource.YOUTUBE)
        self.assertEqual(len(result.tracks), 1)
        self.assertEqual(
            result.tracks[0].identifier,
            "youtube-track"
        )

    async def test_route_queries_only_selected_provider(self) -> None:
        """Verify that later providers are not queried."""

        await QueryRouter.route(
            self.search_query,
            (
                self.youtube_provider,
                self.spotify_provider
            )
        )

        self.assertEqual(
            self.youtube_provider.query_calls,
            [self.search_query]
        )
        self.assertEqual(self.spotify_provider.query_calls, [])

    async def test_route_respects_requested_source(self) -> None:
        """Verify that routing uses the explicitly requested source."""

        result = await QueryRouter.route(
            self.youtube_query,
            (
                self.spotify_provider,
                self.youtube_provider
            )
        )

        self.assertIs(result.source, MediaSource.YOUTUBE)
        self.assertEqual(
            self.youtube_provider.query_calls,
            [self.youtube_query]
        )
        self.assertEqual(self.spotify_provider.query_calls, [])

if __name__ == "__main__":
    unittest.main()
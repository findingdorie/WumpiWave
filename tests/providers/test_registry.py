"""Tests for the WumpiWave metadata provider registry."""

from __future__ import annotations

import unittest
from typing import cast

from wumpiwave.exceptions import (
    ProviderAlreadyRegisteredError,
    ProviderError,
    ProviderNotFoundError,
    UnsupportedQueryError
)
from wumpiwave.models import (
    MediaQuery,
    MediaResult,
    MediaSource,
    QueryType
)
from wumpiwave.protocols import MediaProvider
from wumpiwave.providers.registry import ProviderRegistry

class StubProvider:
    """Provide a configurable metadata provider for registry tests.

    Attributes:
        name:
            The public provider name.
        source:
            The media source represented by the provider.
        supported:
            Whether the provider supports supplied queries.
        query_calls:
            Queries received by the provider.
        close_calls:
            The number of close requests received.
        closed:
            Whether the provider has been closed.
        close_error:
            An optional exception raised during cleanup.
        close_log:
            An optional list recording provider cleanup order.

    Methods:
        supports:
            Return whether the provider supports a query.
        query:
            Process and record a media query.
        close:
            Close the provider or raise its configured exception.
    """

    __slots__ = (
        "close_calls",
        "close_error",
        "close_log",
        "closed",
        "name",
        "query_calls",
        "source",
        "supported"
    )

    name: str
    source: MediaSource
    supported: bool
    query_calls: list[MediaQuery]
    close_calls: int
    closed: bool
    close_error: Exception | None
    close_log: list[str] | None

    def __init__(
        self,
        name: str,
        source: MediaSource,
        *,
        supported: bool = True,
        close_error: Exception | None = None,
        close_log: list[str] | None = None
    ) -> None:
        """Initialize the configurable metadata provider."""

        self.name = name
        self.source = source
        self.supported = supported
        self.query_calls = []
        self.close_calls = 0
        self.closed = False
        self.close_error = close_error
        self.close_log = close_log

    def supports(self, query: MediaQuery) -> bool:
        """Return whether this provider supports the query."""

        return self.supported

    async def query(self, query: MediaQuery) -> MediaResult:
        """Record and process a media query."""

        self.query_calls.append(query)

        return MediaResult(
            query=query,
            source=self.source
        )

    async def close(self) -> None:
        """Close the provider or raise its configured error."""

        self.close_calls += 1

        if self.close_log is not None:
            self.close_log.append(self.name)

        if self.close_error is not None:
            raise self.close_error

        self.closed = True


def as_media_provider(provider: StubProvider) -> MediaProvider:
    """Cast a test provider to the public provider protocol."""

    return cast(MediaProvider, provider)

class ProviderRegistryTestCase(unittest.IsolatedAsyncioTestCase):
    """Test provider registration, lookup, routing, and cleanup."""

    def setUp(self) -> None:
        """Create reusable providers and queries for each test."""

        self.query = MediaQuery(
            value="Example track",
            query_type=QueryType.SEARCH
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

    def test_creates_empty_registry(self) -> None:
        """Verify that a new registry contains no providers."""

        registry = ProviderRegistry()

        self.assertFalse(registry.closed)
        self.assertEqual(registry.names, ())
        self.assertEqual(registry.providers, ())
        self.assertEqual(len(registry), 0)
        self.assertFalse(registry)

    def test_initializes_with_providers_in_order(self) -> None:
        """Verify that initialization preserves provider order."""

        registry = ProviderRegistry(
            (
                as_media_provider(self.youtube_provider),
                as_media_provider(self.spotify_provider)
            )
        )

        self.assertEqual(
            registry.names,
            (
                "youtube",
                "spotify"
            )
        )
        self.assertEqual(
            registry.providers,
            (
                self.youtube_provider,
                self.spotify_provider
            )
        )
        self.assertEqual(len(registry), 2)
        self.assertTrue(registry)

    def test_register_adds_provider(self) -> None:
        """Verify that one provider can be registered."""

        registry = ProviderRegistry()

        result = registry.register(
            as_media_provider(self.youtube_provider)
        )

        self.assertIs(result, registry)
        self.assertEqual(registry.names, ("youtube",))
        self.assertEqual(
            registry.providers,
            (self.youtube_provider,)
        )

    def test_register_rejects_duplicate_name(self) -> None:
        """Verify that duplicate provider names are rejected."""

        registry = ProviderRegistry(
            [as_media_provider(self.youtube_provider)]
        )
        duplicate = StubProvider(
            name="youtube",
            source=MediaSource.YOUTUBE
        )

        with self.assertRaises(ProviderAlreadyRegisteredError):
            registry.register(
                as_media_provider(duplicate)
            )

        self.assertEqual(
            registry.providers,
            (self.youtube_provider,)
        )

    def test_register_rejects_duplicate_name_case_insensitively(
        self
    ) -> None:
        """Verify that normalized duplicate names are rejected."""

        registry = ProviderRegistry(
            [as_media_provider(self.youtube_provider)]
        )
        duplicate = StubProvider(
            name="  YOUTUBE  ",
            source=MediaSource.YOUTUBE
        )

        with self.assertRaises(ProviderAlreadyRegisteredError):
            registry.register(
                as_media_provider(duplicate)
            )

        self.assertEqual(
            registry.providers,
            (self.youtube_provider,)
        )

    def test_register_rejects_empty_name(self) -> None:
        """Verify that provider names cannot be empty."""

        provider = StubProvider(
            name="   ",
            source=MediaSource.HTTP
        )
        registry = ProviderRegistry()

        with self.assertRaises(ValueError):
            registry.register(
                as_media_provider(provider)
            )

        self.assertFalse(registry)

    def test_register_all_adds_providers_atomically(self) -> None:
        """Verify that multiple providers can be registered together."""

        registry = ProviderRegistry()

        result = registry.register_all(
            (
                as_media_provider(self.youtube_provider),
                as_media_provider(self.spotify_provider)
            )
        )

        self.assertIs(result, registry)
        self.assertEqual(
            registry.providers,
            (
                self.youtube_provider,
                self.spotify_provider
            )
        )

    def test_register_all_rejects_duplicate_batch_atomically(
        self
    ) -> None:
        """Verify that duplicate batch names modify nothing."""

        duplicate = StubProvider(
            name="SPOTIFY",
            source=MediaSource.SPOTIFY
        )
        registry = ProviderRegistry(
            [as_media_provider(self.youtube_provider)]
        )

        with self.assertRaises(ProviderAlreadyRegisteredError):
            registry.register_all(
                (
                    as_media_provider(self.spotify_provider),
                    as_media_provider(duplicate)
                )
            )

        self.assertEqual(
            registry.providers,
            (self.youtube_provider,)
        )

    def test_register_all_rejects_existing_name_atomically(
        self
    ) -> None:
        """Verify that existing names prevent partial registration."""

        duplicate = StubProvider(
            name="youtube",
            source=MediaSource.YOUTUBE
        )
        registry = ProviderRegistry(
            [as_media_provider(self.youtube_provider)]
        )

        with self.assertRaises(ProviderAlreadyRegisteredError):
            registry.register_all(
                (
                    as_media_provider(self.spotify_provider),
                    as_media_provider(duplicate)
                )
            )

        self.assertEqual(
            registry.providers,
            (self.youtube_provider,)
        )

    def test_get_returns_provider_case_insensitively(self) -> None:
        """Verify that provider lookup ignores casing and whitespace."""

        registry = ProviderRegistry(
            [as_media_provider(self.youtube_provider)]
        )

        provider = registry.get("  YOUTUBE  ")

        self.assertIs(provider, self.youtube_provider)

    def test_get_rejects_unknown_provider(self) -> None:
        """Verify that unknown provider names raise an error."""

        registry = ProviderRegistry()

        with self.assertRaises(ProviderNotFoundError):
            registry.get("youtube")

    def test_get_rejects_empty_name(self) -> None:
        """Verify that lookup names cannot be empty."""

        registry = ProviderRegistry()

        with self.assertRaises(ValueError):
            registry.get("   ")

    def test_unregister_returns_provider_without_closing_it(
        self
    ) -> None:
        """Verify that unregistering does not close the provider."""

        registry = ProviderRegistry(
            (
                as_media_provider(self.youtube_provider),
                as_media_provider(self.spotify_provider)
            )
        )

        removed_provider = registry.unregister("YOUTUBE")

        self.assertIs(removed_provider, self.youtube_provider)
        self.assertEqual(self.youtube_provider.close_calls, 0)
        self.assertFalse(self.youtube_provider.closed)
        self.assertEqual(
            registry.providers,
            (self.spotify_provider,)
        )

    def test_unregister_rejects_unknown_provider(self) -> None:
        """Verify that unknown providers cannot be unregistered."""

        registry = ProviderRegistry()

        with self.assertRaises(ProviderNotFoundError):
            registry.unregister("youtube")

    def test_select_returns_first_supported_provider(self) -> None:
        """Verify that registration order defines provider priority."""

        registry = ProviderRegistry(
            (
                as_media_provider(self.youtube_provider),
                as_media_provider(self.spotify_provider)
            )
        )

        provider = registry.select(self.query)

        self.assertIs(provider, self.youtube_provider)

    def test_select_skips_unsupported_providers(self) -> None:
        """Verify that unsupported providers are skipped."""

        self.youtube_provider.supported = False
        registry = ProviderRegistry(
            (
                as_media_provider(self.youtube_provider),
                as_media_provider(self.spotify_provider)
            )
        )

        provider = registry.select(self.query)

        self.assertIs(provider, self.spotify_provider)

    def test_select_rejects_unsupported_query(self) -> None:
        """Verify that missing provider support raises an error."""

        self.youtube_provider.supported = False
        self.spotify_provider.supported = False
        registry = ProviderRegistry(
            (
                as_media_provider(self.youtube_provider),
                as_media_provider(self.spotify_provider)
            )
        )

        with self.assertRaises(UnsupportedQueryError):
            registry.select(self.query)

    def test_supports_returns_expected_state(self) -> None:
        """Verify that query support reflects registered providers."""

        self.youtube_provider.supported = False
        registry = ProviderRegistry(
            (
                as_media_provider(self.youtube_provider),
                as_media_provider(self.spotify_provider)
            )
        )

        self.assertTrue(registry.supports(self.query))

        self.spotify_provider.supported = False

        self.assertFalse(registry.supports(self.query))

    async def test_query_routes_to_selected_provider(self) -> None:
        """Verify that queries are routed to the first compatible provider."""

        registry = ProviderRegistry(
            (
                as_media_provider(self.youtube_provider),
                as_media_provider(self.spotify_provider)
            )
        )

        result = await registry.query(self.query)

        self.assertIs(result.query, self.query)
        self.assertIs(result.source, MediaSource.YOUTUBE)
        self.assertEqual(
            self.youtube_provider.query_calls,
            [self.query]
        )
        self.assertEqual(
            self.spotify_provider.query_calls,
            []
        )

    async def test_close_closes_providers_in_reverse_order(
        self
    ) -> None:
        """Verify that cleanup follows reverse registration order."""

        close_log: list[str] = []
        youtube_provider = StubProvider(
            name="youtube",
            source=MediaSource.YOUTUBE,
            close_log=close_log
        )
        spotify_provider = StubProvider(
            name="spotify",
            source=MediaSource.SPOTIFY,
            close_log=close_log
        )
        http_provider = StubProvider(
            name="http",
            source=MediaSource.HTTP,
            close_log=close_log
        )
        registry = ProviderRegistry(
            (
                as_media_provider(youtube_provider),
                as_media_provider(spotify_provider),
                as_media_provider(http_provider)
            )
        )

        await registry.close()

        self.assertEqual(
            close_log,
            [
                "http",
                "spotify",
                "youtube"
            ]
        )
        self.assertTrue(registry.closed)
        self.assertEqual(registry.providers, ())
        self.assertEqual(len(registry), 0)

    async def test_close_is_idempotent(self) -> None:
        """Verify that repeated cleanup does not close providers twice."""

        registry = ProviderRegistry(
            [as_media_provider(self.youtube_provider)]
        )

        await registry.close()
        await registry.close()

        self.assertEqual(self.youtube_provider.close_calls, 1)

    async def test_close_continues_after_provider_failure(self) -> None:
        """Verify that one cleanup failure does not skip providers."""

        failing_provider = StubProvider(
            name="spotify",
            source=MediaSource.SPOTIFY,
            close_error=RuntimeError("Close failed.")
        )
        registry = ProviderRegistry(
            (
                as_media_provider(self.youtube_provider),
                as_media_provider(failing_provider),
                as_media_provider(self.http_provider)
            )
        )

        with self.assertRaises(ExceptionGroup):
            await registry.close()

        self.assertTrue(registry.closed)
        self.assertEqual(registry.providers, ())
        self.assertEqual(self.youtube_provider.close_calls, 1)
        self.assertEqual(failing_provider.close_calls, 1)
        self.assertEqual(self.http_provider.close_calls, 1)

    async def test_closed_registry_rejects_operations(self) -> None:
        """Verify that a closed registry cannot be used again."""

        registry = ProviderRegistry(
            [as_media_provider(self.youtube_provider)]
        )

        await registry.close()

        with self.assertRaises(ProviderError):
            registry.register(
                as_media_provider(self.spotify_provider)
            )

        with self.assertRaises(ProviderError):
            registry.get("youtube")

        with self.assertRaises(ProviderError):
            registry.unregister("youtube")

        with self.assertRaises(ProviderError):
            registry.select(self.query)

        with self.assertRaises(ProviderError):
            await registry.query(self.query)

        self.assertFalse(registry.supports(self.query))

    def test_contains_supports_normalized_names(self) -> None:
        """Verify that membership checks ignore casing and whitespace."""

        registry = ProviderRegistry(
            [as_media_provider(self.youtube_provider)]
        )

        self.assertIn("youtube", registry)
        self.assertIn("  YOUTUBE  ", registry)
        self.assertNotIn("spotify", registry)
        self.assertNotIn("", registry)
        self.assertNotIn(object(), registry)

    def test_iteration_preserves_registration_order(self) -> None:
        """Verify that iteration follows provider priority order."""

        registry = ProviderRegistry(
            (
                as_media_provider(self.youtube_provider),
                as_media_provider(self.spotify_provider),
                as_media_provider(self.http_provider)
            )
        )

        self.assertEqual(
            tuple(registry),
            (
                self.youtube_provider,
                self.spotify_provider,
                self.http_provider
            )
        )

    async def test_async_context_manager_closes_registry(self) -> None:
        """Verify that leaving the context closes all providers."""

        registry = ProviderRegistry(
            [as_media_provider(self.youtube_provider)]
        )

        async with registry as active_registry:
            self.assertIs(active_registry, registry)
            self.assertFalse(registry.closed)

        self.assertTrue(registry.closed)
        self.assertTrue(self.youtube_provider.closed)

    async def test_closed_registry_cannot_enter_context(self) -> None:
        """Verify that closed registries cannot be entered again."""

        registry = ProviderRegistry()

        await registry.close()

        with self.assertRaises(ProviderError):
            async with registry:
                self.fail("A closed registry entered its context.")

if __name__ == "__main__":
    unittest.main()
"""Tests for the WumpiWave stream resolver registry."""

from __future__ import annotations

import unittest
from typing import cast

from wumpiwave.exceptions import (
    ResolverAlreadyRegisteredError,
    ResolverError,
    ResolverNotFoundError,
    UnsupportedMediaError
)
from wumpiwave.models import (
    MediaSource,
    MediaTrack,
    PlayableSource
)
from wumpiwave.protocols import StreamResolver
from wumpiwave.resolvers.registry import ResolverRegistry

class StubResolver:
    """Provide a configurable stream resolver for registry tests.

    Attributes:
        name:
            The public resolver name.
        supported:
            Whether the resolver supports supplied tracks.
        source:
            The playable source returned during resolution.
        resolve_calls:
            Tracks received by the resolver.
        close_calls:
            The number of close requests received.
        closed:
            Whether the resolver has been closed.
        close_error:
            An optional exception raised during cleanup.
        close_log:
            An optional list recording cleanup order.

    Methods:
        supports:
            Return whether the resolver supports a track.
        resolve:
            Resolve and record a media track.
        close:
            Close the resolver or raise its configured exception.
    """

    __slots__ = (
        "close_calls",
        "close_error",
        "close_log",
        "closed",
        "name",
        "resolve_calls",
        "source",
        "supported"
    )

    name: str
    supported: bool
    source: PlayableSource
    resolve_calls: list[MediaTrack]
    close_calls: int
    closed: bool
    close_error: Exception | None
    close_log: list[str] | None

    def __init__(
        self,
        name: str,
        source: PlayableSource,
        *,
        supported: bool = True,
        close_error: Exception | None = None,
        close_log: list[str] | None = None
    ) -> None:
        """Initialize the configurable stream resolver."""

        self.name = name
        self.supported = supported
        self.source = source
        self.resolve_calls = []
        self.close_calls = 0
        self.closed = False
        self.close_error = close_error
        self.close_log = close_log

    def supports(self, track: MediaTrack) -> bool:
        """Return whether this resolver supports the track."""

        return self.supported

    async def resolve(self, track: MediaTrack) -> PlayableSource:
        """Record the track and return the configured playable source."""

        self.resolve_calls.append(track)
        return self.source

    async def close(self) -> None:
        """Close the resolver or raise its configured error."""

        self.close_calls += 1

        if self.close_log is not None:
            self.close_log.append(self.name)

        if self.close_error is not None:
            raise self.close_error

        self.closed = True


def as_stream_resolver(resolver: StubResolver) -> StreamResolver:
    """Cast a test resolver to the public resolver protocol."""

    return cast(StreamResolver, resolver)

class ResolverRegistryTestCase(unittest.IsolatedAsyncioTestCase):
    """Test resolver registration, lookup, selection, and cleanup."""

    def setUp(self) -> None:
        """Create reusable tracks, sources, and resolvers."""

        self.track = MediaTrack(
            identifier="track-id",
            source=MediaSource.YOUTUBE,
            title="Example track",
            url="https://www.youtube.com/watch?v=track-id"
        )
        self.youtube_source = PlayableSource(
            stream_url="https://example.com/youtube-audio",
            source=MediaSource.YOUTUBE
        )
        self.spotify_source = PlayableSource(
            stream_url="https://example.com/spotify-audio",
            source=MediaSource.YOUTUBE
        )
        self.http_source = PlayableSource(
            stream_url="https://example.com/audio.mp3",
            source=MediaSource.HTTP
        )
        self.youtube_resolver = StubResolver(
            name="youtube",
            source=self.youtube_source
        )
        self.spotify_resolver = StubResolver(
            name="spotify",
            source=self.spotify_source
        )
        self.http_resolver = StubResolver(
            name="http",
            source=self.http_source
        )

    def test_creates_empty_registry(self) -> None:
        """Verify that a new registry contains no resolvers."""

        registry = ResolverRegistry()

        self.assertFalse(registry.closed)
        self.assertEqual(registry.names, ())
        self.assertEqual(registry.resolvers, ())
        self.assertEqual(len(registry), 0)

    def test_initializes_with_resolvers_in_order(self) -> None:
        """Verify that initialization preserves resolver order."""

        registry = ResolverRegistry(
            (
                as_stream_resolver(self.youtube_resolver),
                as_stream_resolver(self.spotify_resolver)
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
            registry.resolvers,
            (
                self.youtube_resolver,
                self.spotify_resolver
            )
        )
        self.assertEqual(len(registry), 2)

    def test_register_adds_resolver(self) -> None:
        """Verify that one resolver can be registered."""

        registry = ResolverRegistry()

        result = registry.register(
            as_stream_resolver(self.youtube_resolver)
        )

        self.assertIs(result, registry)
        self.assertEqual(registry.names, ("youtube",))
        self.assertEqual(
            registry.resolvers,
            (self.youtube_resolver,)
        )

    def test_register_rejects_duplicate_name(self) -> None:
        """Verify that duplicate resolver names are rejected."""

        registry = ResolverRegistry(
            [as_stream_resolver(self.youtube_resolver)]
        )
        duplicate = StubResolver(
            name="youtube",
            source=self.youtube_source
        )

        with self.assertRaises(ResolverAlreadyRegisteredError):
            registry.register(
                as_stream_resolver(duplicate)
            )

        self.assertEqual(
            registry.resolvers,
            (self.youtube_resolver,)
        )

    def test_register_rejects_duplicate_name_case_insensitively(
        self
    ) -> None:
        """Verify that normalized duplicate names are rejected."""

        registry = ResolverRegistry(
            [as_stream_resolver(self.youtube_resolver)]
        )
        duplicate = StubResolver(
            name="  YOUTUBE  ",
            source=self.youtube_source
        )

        with self.assertRaises(ResolverAlreadyRegisteredError):
            registry.register(
                as_stream_resolver(duplicate)
            )

        self.assertEqual(
            registry.resolvers,
            (self.youtube_resolver,)
        )

    def test_register_rejects_empty_name(self) -> None:
        """Verify that resolver names cannot be empty."""

        resolver = StubResolver(
            name="   ",
            source=self.http_source
        )
        registry = ResolverRegistry()

        with self.assertRaises(ValueError):
            registry.register(
                as_stream_resolver(resolver)
            )

        self.assertEqual(registry.resolvers, ())

    def test_register_all_adds_resolvers_atomically(self) -> None:
        """Verify that multiple resolvers can be registered together."""

        registry = ResolverRegistry()

        result = registry.register_all(
            (
                as_stream_resolver(self.youtube_resolver),
                as_stream_resolver(self.spotify_resolver)
            )
        )

        self.assertIs(result, registry)
        self.assertEqual(
            registry.resolvers,
            (
                self.youtube_resolver,
                self.spotify_resolver
            )
        )

    def test_register_all_rejects_duplicate_batch_atomically(
        self
    ) -> None:
        """Verify that duplicate batch names modify nothing."""

        duplicate = StubResolver(
            name="SPOTIFY",
            source=self.spotify_source
        )
        registry = ResolverRegistry(
            [as_stream_resolver(self.youtube_resolver)]
        )

        with self.assertRaises(ResolverAlreadyRegisteredError):
            registry.register_all(
                (
                    as_stream_resolver(self.spotify_resolver),
                    as_stream_resolver(duplicate)
                )
            )

        self.assertEqual(
            registry.resolvers,
            (self.youtube_resolver,)
        )

    def test_register_all_rejects_existing_name_atomically(
        self
    ) -> None:
        """Verify that existing names prevent partial registration."""

        duplicate = StubResolver(
            name="youtube",
            source=self.youtube_source
        )
        registry = ResolverRegistry(
            [as_stream_resolver(self.youtube_resolver)]
        )

        with self.assertRaises(ResolverAlreadyRegisteredError):
            registry.register_all(
                (
                    as_stream_resolver(self.spotify_resolver),
                    as_stream_resolver(duplicate)
                )
            )

        self.assertEqual(
            registry.resolvers,
            (self.youtube_resolver,)
        )

    def test_get_returns_resolver_case_insensitively(self) -> None:
        """Verify that lookup ignores casing and whitespace."""

        registry = ResolverRegistry(
            [as_stream_resolver(self.youtube_resolver)]
        )

        resolver = registry.get("  YOUTUBE  ")

        self.assertIs(resolver, self.youtube_resolver)

    def test_get_rejects_unknown_resolver(self) -> None:
        """Verify that unknown resolver names raise an error."""

        registry = ResolverRegistry()

        with self.assertRaises(ResolverNotFoundError):
            registry.get("youtube")

    def test_get_rejects_empty_name(self) -> None:
        """Verify that lookup names cannot be empty."""

        registry = ResolverRegistry()

        with self.assertRaises(ValueError):
            registry.get("   ")

    def test_unregister_returns_resolver_without_closing_it(
        self
    ) -> None:
        """Verify that unregistering does not close the resolver."""

        registry = ResolverRegistry(
            (
                as_stream_resolver(self.youtube_resolver),
                as_stream_resolver(self.spotify_resolver)
            )
        )

        removed_resolver = registry.unregister("YOUTUBE")

        self.assertIs(removed_resolver, self.youtube_resolver)
        self.assertEqual(self.youtube_resolver.close_calls, 0)
        self.assertFalse(self.youtube_resolver.closed)
        self.assertEqual(
            registry.resolvers,
            (self.spotify_resolver,)
        )

    def test_unregister_rejects_unknown_resolver(self) -> None:
        """Verify that unknown resolvers cannot be removed."""

        registry = ResolverRegistry()

        with self.assertRaises(ResolverNotFoundError):
            registry.unregister("youtube")

    def test_select_returns_first_supported_resolver(self) -> None:
        """Verify that registration order defines resolver priority."""

        registry = ResolverRegistry(
            (
                as_stream_resolver(self.youtube_resolver),
                as_stream_resolver(self.spotify_resolver)
            )
        )

        resolver = registry.select(self.track)

        self.assertIs(resolver, self.youtube_resolver)

    def test_select_skips_unsupported_resolvers(self) -> None:
        """Verify that unsupported resolvers are skipped."""

        self.youtube_resolver.supported = False
        registry = ResolverRegistry(
            (
                as_stream_resolver(self.youtube_resolver),
                as_stream_resolver(self.spotify_resolver)
            )
        )

        resolver = registry.select(self.track)

        self.assertIs(resolver, self.spotify_resolver)

    def test_select_rejects_unsupported_track(self) -> None:
        """Verify that missing resolver support raises an error."""

        self.youtube_resolver.supported = False
        self.spotify_resolver.supported = False
        registry = ResolverRegistry(
            (
                as_stream_resolver(self.youtube_resolver),
                as_stream_resolver(self.spotify_resolver)
            )
        )

        with self.assertRaises(UnsupportedMediaError):
            registry.select(self.track)

    def test_supports_returns_expected_state(self) -> None:
        """Verify that support reflects registered resolvers."""

        self.youtube_resolver.supported = False
        registry = ResolverRegistry(
            (
                as_stream_resolver(self.youtube_resolver),
                as_stream_resolver(self.spotify_resolver)
            )
        )

        self.assertTrue(registry.supports(self.track))

        self.spotify_resolver.supported = False

        self.assertFalse(registry.supports(self.track))

    async def test_resolve_routes_to_selected_resolver(self) -> None:
        """Verify that tracks are routed to a compatible resolver."""

        registry = ResolverRegistry(
            (
                as_stream_resolver(self.youtube_resolver),
                as_stream_resolver(self.spotify_resolver)
            )
        )

        source = await registry.resolve(self.track)

        self.assertIs(source, self.youtube_source)
        self.assertEqual(
            self.youtube_resolver.resolve_calls,
            [self.track]
        )
        self.assertEqual(
            self.spotify_resolver.resolve_calls,
            []
        )

    async def test_close_closes_resolvers_in_registration_order(
        self
    ) -> None:
        """Verify that cleanup follows registration order."""

        close_log: list[str] = []
        youtube_resolver = StubResolver(
            name="youtube",
            source=self.youtube_source,
            close_log=close_log
        )
        spotify_resolver = StubResolver(
            name="spotify",
            source=self.spotify_source,
            close_log=close_log
        )
        http_resolver = StubResolver(
            name="http",
            source=self.http_source,
            close_log=close_log
        )
        registry = ResolverRegistry(
            (
                as_stream_resolver(youtube_resolver),
                as_stream_resolver(spotify_resolver),
                as_stream_resolver(http_resolver)
            )
        )

        await registry.close()

        self.assertEqual(
            close_log,
            [
                "youtube",
                "spotify",
                "http"
            ]
        )
        self.assertTrue(registry.closed)
        self.assertEqual(registry.resolvers, ())
        self.assertEqual(len(registry), 0)

    async def test_close_is_idempotent(self) -> None:
        """Verify that repeated cleanup does not close resolvers twice."""

        registry = ResolverRegistry(
            [as_stream_resolver(self.youtube_resolver)]
        )

        await registry.close()
        await registry.close()

        self.assertEqual(self.youtube_resolver.close_calls, 1)

    async def test_close_continues_after_resolver_failure(self) -> None:
        """Verify that one cleanup failure does not skip resolvers."""

        failing_resolver = StubResolver(
            name="spotify",
            source=self.spotify_source,
            close_error=RuntimeError("Close failed.")
        )
        registry = ResolverRegistry(
            (
                as_stream_resolver(self.youtube_resolver),
                as_stream_resolver(failing_resolver),
                as_stream_resolver(self.http_resolver)
            )
        )

        with self.assertRaises(ExceptionGroup):
            await registry.close()

        self.assertTrue(registry.closed)
        self.assertEqual(registry.resolvers, ())
        self.assertEqual(self.youtube_resolver.close_calls, 1)
        self.assertEqual(failing_resolver.close_calls, 1)
        self.assertEqual(self.http_resolver.close_calls, 1)

    async def test_closed_registry_rejects_operations(self) -> None:
        """Verify that a closed registry cannot be used again."""

        registry = ResolverRegistry(
            [as_stream_resolver(self.youtube_resolver)]
        )

        await registry.close()

        with self.assertRaises(ResolverError):
            registry.register(
                as_stream_resolver(self.spotify_resolver)
            )

        with self.assertRaises(ResolverError):
            registry.get("youtube")

        with self.assertRaises(ResolverError):
            registry.unregister("youtube")

        with self.assertRaises(ResolverError):
            registry.select(self.track)

        with self.assertRaises(ResolverError):
            await registry.resolve(self.track)

        self.assertFalse(registry.supports(self.track))

    def test_contains_supports_normalized_names(self) -> None:
        """Verify that membership ignores casing and whitespace."""

        registry = ResolverRegistry(
            [as_stream_resolver(self.youtube_resolver)]
        )

        self.assertIn("youtube", registry)
        self.assertIn("  YOUTUBE  ", registry)
        self.assertNotIn("spotify", registry)
        self.assertNotIn("", registry)
        self.assertNotIn(object(), registry)

    def test_iteration_preserves_registration_order(self) -> None:
        """Verify that iteration follows resolver priority order."""

        registry = ResolverRegistry(
            (
                as_stream_resolver(self.youtube_resolver),
                as_stream_resolver(self.spotify_resolver),
                as_stream_resolver(self.http_resolver)
            )
        )

        self.assertEqual(
            tuple(registry),
            (
                self.youtube_resolver,
                self.spotify_resolver,
                self.http_resolver
            )
        )

    async def test_async_context_manager_closes_registry(self) -> None:
        """Verify that leaving the context closes all resolvers."""

        registry = ResolverRegistry(
            [as_stream_resolver(self.youtube_resolver)]
        )

        async with registry as active_registry:
            self.assertIs(active_registry, registry)
            self.assertFalse(registry.closed)

        self.assertTrue(registry.closed)
        self.assertTrue(self.youtube_resolver.closed)

    async def test_closed_registry_cannot_enter_context(self) -> None:
        """Verify that a closed registry cannot be entered again."""

        registry = ResolverRegistry()

        await registry.close()

        with self.assertRaises(ResolverError):
            async with registry:
                self.fail("A closed registry entered its context.")

if __name__ == "__main__":
    unittest.main()
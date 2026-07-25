"""Tests for the WumpiWave media player registry."""

from __future__ import annotations

import unittest
from typing import cast

from wumpiwave.exceptions import (
    PlayerAlreadyExistsError,
    PlayerDestroyedError,
    PlayerNotFoundError,
)
from wumpiwave.playback.registry import PlayerRegistry
from wumpiwave.protocols import MediaPlayer

class StubMediaPlayer:
    """Provide a configurable media player for registry tests.

    Attributes:
        identifier:
            The numeric identifier used by the registry.
        destroyed:
            Whether the player has been destroyed.
        destroy_calls:
            The number of destruction requests received.
        destroy_error:
            An optional exception raised during destruction.
        destruction_log:
            An optional list recording destruction order.

    Methods:
        destroy:
            Mark the player as destroyed or raise its configured error.
    """

    __slots__ = (
        "destroy_calls",
        "destroy_error",
        "destroyed",
        "destruction_log",
        "identifier",
    )

    identifier: int
    destroyed: bool
    destroy_calls: int
    destroy_error: Exception | None
    destruction_log: list[int] | None

    def __init__(
        self,
        identifier: int,
        *,
        destroyed: bool = False,
        destroy_error: Exception | None = None,
        destruction_log: list[int] | None = None
    ) -> None:
        """Initialize the configurable media player."""

        self.identifier = identifier
        self.destroyed = destroyed
        self.destroy_calls = 0
        self.destroy_error = destroy_error
        self.destruction_log = destruction_log

    async def destroy(self) -> None:
        """Destroy the player or raise its configured error."""

        self.destroy_calls += 1

        if self.destruction_log is not None:
            self.destruction_log.append(self.identifier)

        if self.destroy_error is not None:
            raise self.destroy_error

        self.destroyed = True


def as_media_player(player: StubMediaPlayer) -> MediaPlayer:
    """Cast a test player to the public media player protocol."""

    return cast(MediaPlayer, player)

class PlayerRegistryTestCase(unittest.IsolatedAsyncioTestCase):
    """Test media player registration, lookup, removal, and cleanup."""

    def setUp(self) -> None:
        """Create reusable media players for each test."""

        self.first_player = StubMediaPlayer(100)
        self.second_player = StubMediaPlayer(200)
        self.third_player = StubMediaPlayer(300)

    def test_creates_empty_registry(self) -> None:
        """Verify that a new registry contains no players."""

        registry = PlayerRegistry()

        self.assertEqual(registry.identifiers, ())
        self.assertEqual(registry.players, ())
        self.assertEqual(registry.size, 0)
        self.assertTrue(registry.is_empty)
        self.assertEqual(len(registry), 0)
        self.assertFalse(registry)

    def test_initializes_with_players_in_order(self) -> None:
        """Verify that initialization preserves registration order."""

        registry = PlayerRegistry(
            (
                as_media_player(self.first_player),
                as_media_player(self.second_player)
            )
        )

        self.assertEqual(
            registry.identifiers,
            (
                100,
                200
            )
        )
        self.assertEqual(
            registry.players,
            (
                self.first_player,
                self.second_player
            )
        )
        self.assertEqual(registry.size, 2)
        self.assertFalse(registry.is_empty)
        self.assertTrue(registry)

    def test_register_adds_player(self) -> None:
        """Verify that one media player can be registered."""

        registry = PlayerRegistry()

        result = registry.register(as_media_player(self.first_player))

        self.assertIs(result, registry)
        self.assertEqual(registry.identifiers, (100,))
        self.assertEqual(
            registry.players,
            (self.first_player,)
        )

    def test_register_rejects_duplicate_identifier(self) -> None:
        """Verify that duplicate player identifiers are rejected."""

        registry = PlayerRegistry(
            (as_media_player(self.first_player),)
        )
        duplicate = StubMediaPlayer(100)

        with self.assertRaises(PlayerAlreadyExistsError):
            registry.register(as_media_player(duplicate))

        self.assertEqual(
            registry.players,
            (self.first_player,)
        )

    def test_register_rejects_destroyed_player(self) -> None:
        """Verify that destroyed players cannot be registered."""

        registry = PlayerRegistry()
        destroyed_player = StubMediaPlayer(
            100,
            destroyed=True
        )

        with self.assertRaises(PlayerDestroyedError):
            registry.register(as_media_player(destroyed_player))

        self.assertTrue(registry.is_empty)

    def test_register_rejects_boolean_identifier(self) -> None:
        """Verify that booleans are not valid player identifiers."""

        registry = PlayerRegistry()
        player = StubMediaPlayer(cast(int, True))

        with self.assertRaises(TypeError):
            registry.register(as_media_player(player))

        self.assertTrue(registry.is_empty)

    def test_register_rejects_non_integer_identifier(self) -> None:
        """Verify that player identifiers must be integers."""

        registry = PlayerRegistry()
        player = StubMediaPlayer(cast(int, "100"))

        with self.assertRaises(TypeError):
            registry.register(as_media_player(player))

        self.assertTrue(registry.is_empty)

    def test_register_all_adds_players_atomically(self) -> None:
        """Verify that multiple players can be registered together."""

        registry = PlayerRegistry()

        result = registry.register_all(
            (
                as_media_player(self.first_player),
                as_media_player(self.second_player)
            )
        )

        self.assertIs(result, registry)
        self.assertEqual(
            registry.players,
            (
                self.first_player,
                self.second_player
            )
        )

    def test_register_all_rejects_duplicate_in_batch(self) -> None:
        """Verify that duplicate batch identifiers modify nothing."""

        registry = PlayerRegistry(
            (as_media_player(self.first_player),)
        )
        second_player = StubMediaPlayer(200)
        duplicate = StubMediaPlayer(200)

        with self.assertRaises(PlayerAlreadyExistsError):
            registry.register_all(
                (
                    as_media_player(second_player),
                    as_media_player(duplicate)
                )
            )

        self.assertEqual(
            registry.players,
            (self.first_player,)
        )

    def test_register_all_rejects_existing_identifier_atomically(self) -> None:
        """Verify that existing identifiers prevent partial registration."""

        registry = PlayerRegistry(
            (as_media_player(self.first_player),)
        )
        duplicate = StubMediaPlayer(100)

        with self.assertRaises(PlayerAlreadyExistsError):
            registry.register_all(
                (
                    as_media_player(self.second_player),
                    as_media_player(duplicate)
                )
            )

        self.assertEqual(
            registry.players,
            (self.first_player,)
        )

    def test_register_all_rejects_destroyed_player_atomically(self) -> None:
        """Verify that destroyed batch players modify nothing."""

        registry = PlayerRegistry(
            (as_media_player(self.first_player),)
        )
        destroyed_player = StubMediaPlayer(
            300,
            destroyed=True
        )

        with self.assertRaises(PlayerDestroyedError):
            registry.register_all(
                (
                    as_media_player(self.second_player),
                    as_media_player(destroyed_player)
                )
            )

        self.assertEqual(
            registry.players,
            (self.first_player,)
        )

    def test_get_returns_registered_player(self) -> None:
        """Verify that players can be retrieved by identifier."""

        registry = PlayerRegistry(
            (as_media_player(self.first_player),)
        )

        player = registry.get(100)

        self.assertIs(player, self.first_player)

    def test_get_rejects_unknown_identifier(self) -> None:
        """Verify that unknown identifiers raise an error."""

        registry = PlayerRegistry()

        with self.assertRaises(PlayerNotFoundError):
            registry.get(100)

    def test_get_rejects_invalid_identifier_type(self) -> None:
        """Verify that lookup identifiers must be integers."""

        registry = PlayerRegistry()

        with self.assertRaises(TypeError):
            registry.get("100")  # type: ignore[arg-type]

    def test_remove_returns_player_without_destroying_it(self) -> None:
        """Verify that removal does not destroy the media player."""

        registry = PlayerRegistry(
            (
                as_media_player(self.first_player),
                as_media_player(self.second_player)
            )
        )

        removed_player = registry.remove(100)

        self.assertIs(removed_player, self.first_player)
        self.assertEqual(self.first_player.destroy_calls, 0)
        self.assertFalse(self.first_player.destroyed)
        self.assertEqual(
            registry.players,
            (self.second_player,)
        )

    def test_remove_rejects_unknown_identifier(self) -> None:
        """Verify that unknown players cannot be removed."""

        registry = PlayerRegistry()

        with self.assertRaises(PlayerNotFoundError):
            registry.remove(100)

    async def test_destroy_removes_and_destroys_player(self) -> None:
        """Verify that destruction removes and cleans up a player."""

        registry = PlayerRegistry(
            (as_media_player(self.first_player),)
        )

        await registry.destroy(100)

        self.assertTrue(registry.is_empty)
        self.assertEqual(self.first_player.destroy_calls, 1)
        self.assertTrue(self.first_player.destroyed)

    async def test_destroy_removes_player_before_failure(self) -> None:
        """Verify that failed destruction still removes the player."""

        failing_player = StubMediaPlayer(
            100,
            destroy_error=RuntimeError("Destroy failed.")
        )
        registry = PlayerRegistry(
            (as_media_player(failing_player),)
        )

        with self.assertRaises(RuntimeError):
            await registry.destroy(100)

        self.assertTrue(registry.is_empty)
        self.assertEqual(failing_player.destroy_calls, 1)

    async def test_destroy_all_uses_reverse_registration_order(self) -> None:
        """Verify that all players are destroyed in reverse order."""

        destruction_log: list[int] = []
        first_player = StubMediaPlayer(
            100,
            destruction_log=destruction_log
        )
        second_player = StubMediaPlayer(
            200,
            destruction_log=destruction_log
        )
        third_player = StubMediaPlayer(
            300,
            destruction_log=destruction_log
        )
        registry = PlayerRegistry(
            (
                as_media_player(first_player),
                as_media_player(second_player),
                as_media_player(third_player)
            )
        )

        await registry.destroy_all()

        self.assertEqual(
            destruction_log,
            [
                300,
                200,
                100
            ]
        )
        self.assertTrue(registry.is_empty)
        self.assertTrue(first_player.destroyed)
        self.assertTrue(second_player.destroyed)
        self.assertTrue(third_player.destroyed)

    async def test_destroy_all_continues_after_failure(self) -> None:
        """Verify that one failure does not skip other players."""

        failing_player = StubMediaPlayer(
            200,
            destroy_error=RuntimeError("Destroy failed.")
        )
        registry = PlayerRegistry(
            (
                as_media_player(self.first_player),
                as_media_player(failing_player),
                as_media_player(self.third_player)
            )
        )

        with self.assertRaises(ExceptionGroup):
            await registry.destroy_all()

        self.assertTrue(registry.is_empty)
        self.assertEqual(self.first_player.destroy_calls, 1)
        self.assertEqual(failing_player.destroy_calls, 1)
        self.assertEqual(self.third_player.destroy_calls, 1)
        self.assertTrue(self.first_player.destroyed)
        self.assertTrue(self.third_player.destroyed)

    def test_clear_returns_players_without_destroying_them(self) -> None:
        """Verify that clearing transfers cleanup responsibility."""

        registry = PlayerRegistry(
            (
                as_media_player(self.first_player),
                as_media_player(self.second_player)
            )
        )

        removed_players = registry.clear()

        self.assertEqual(
            removed_players,
            (
                self.first_player,
                self.second_player
            )
        )
        self.assertTrue(registry.is_empty)
        self.assertEqual(self.first_player.destroy_calls, 0)
        self.assertEqual(self.second_player.destroy_calls, 0)

    def test_contains_supports_registered_integer_identifier(self) -> None:
        """Verify that integer identifiers support membership checks."""

        registry = PlayerRegistry(
            (as_media_player(self.first_player),)
        )

        self.assertIn(100, registry)
        self.assertNotIn(200, registry)

    def test_contains_rejects_boolean_and_other_types(self) -> None:
        """Verify that unsupported identifier types return false."""

        registry = PlayerRegistry(
            (as_media_player(self.first_player),)
        )

        self.assertNotIn(True, registry)
        self.assertNotIn("100", registry)
        self.assertNotIn(100.0, registry)
        self.assertNotIn(object(), registry)

    def test_getitem_returns_registered_player(self) -> None:
        """Verify that subscription delegates to player lookup."""

        registry = PlayerRegistry(
            (as_media_player(self.first_player),)
        )

        self.assertIs(registry[100], self.first_player)

    def test_iteration_preserves_registration_order(self) -> None:
        """Verify that iteration follows registration order."""

        registry = PlayerRegistry(
            (
                as_media_player(self.first_player),
                as_media_player(self.second_player),
                as_media_player(self.third_player)
            )
        )

        self.assertEqual(
            tuple(registry),
            (
                self.first_player,
                self.second_player,
                self.third_player
            )
        )

if __name__ == "__main__":
    unittest.main()
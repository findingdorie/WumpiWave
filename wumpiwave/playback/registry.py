"""Media player registry used by WumpiWave.

This module manages media player registration, lookup, removal, destruction,
and bulk cleanup by numeric player identifiers.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Self

from ..exceptions import (
    PlayerAlreadyExistsError,
    PlayerDestroyedError,
    PlayerNotFoundError,
)
from ..protocols import MediaPlayer

class PlayerRegistry:
    """Manage active WumpiWave media players.

    Players are stored by their numeric identifiers while preserving their
    registration order. A player identifier may only belong to one registered
    player at a time.

    Removing a player does not destroy it. Destruction must be requested
    explicitly through ``destroy`` or ``destroy_all``.

    Attributes:
        identifiers:
            The identifiers of all registered players.
        players:
            The registered players in registration order.
        size:
            The number of registered players.
        is_empty:
            Whether no players are currently registered.

    Methods:
        register:
            Register one media player.
        register_all:
            Register multiple media players atomically.
        get:
            Return a player by its identifier.
        remove:
            Remove and return a player without destroying it.
        destroy:
            Remove and destroy one player.
        destroy_all:
            Remove and destroy every registered player.
        clear:
            Remove and return every player without destroying them.
        __contains__:
            Determine whether a player identifier is registered.
        __getitem__:
            Return a registered player by identifier.
        __iter__:
            Iterate over registered players.
        __len__:
            Return the number of registered players.
        __bool__:
            Return whether the registry contains any players.
        _validate_identifier:
            Validate a player identifier.
    """

    __slots__ = ("_players",)

    _players: dict[int, MediaPlayer]

    def __init__(self, players: Iterable[MediaPlayer] = ()) -> None:
        """Initialize a media player registry.

        Args:
            players:
                The media players registered during initialization.

        Raises:
            PlayerAlreadyExistsError:
                Multiple players use the same identifier.
            PlayerDestroyedError:
                A supplied player has already been destroyed.
            TypeError:
                A supplied player identifier is not an integer.
        """

        self._players = {}
        self.register_all(players)

    @property
    def identifiers(self) -> tuple[int, ...]:
        """Return all registered player identifiers.

        Returns:
            The identifiers in their registration order.
        """

        return tuple(self._players)

    @property
    def players(self) -> tuple[MediaPlayer, ...]:
        """Return all registered media players.

        Returns:
            The players in their registration order.
        """

        return tuple(self._players.values())

    @property
    def size(self) -> int:
        """Return the number of registered players.

        Returns:
            The current registry size.
        """

        return len(self._players)

    @property
    def is_empty(self) -> bool:
        """Return whether the registry contains no players.

        Returns:
            ``True`` when no players are registered.
        """

        return not self._players

    def register(self, player: MediaPlayer) -> Self:
        """Register one media player.

        Args:
            player:
                The media player to register.

        Returns:
            The registry instance for chained registrations.

        Raises:
            PlayerAlreadyExistsError:
                The player identifier is already registered.
            PlayerDestroyedError:
                The supplied player has already been destroyed.
            TypeError:
                The player identifier is not an integer.
        """

        player_identifier: int = self._validate_identifier(player.identifier)

        if player.destroyed:
            raise PlayerDestroyedError

        if player_identifier in self._players:
            raise PlayerAlreadyExistsError(player_identifier=player_identifier)

        self._players[player_identifier] = player
        return self

    def register_all(self, players: Iterable[MediaPlayer]) -> Self:
        """Register multiple media players atomically.

        Every supplied player is validated before the registry is modified.
        This prevents partial registration when one player is invalid.

        Args:
            players:
                The media players to register.

        Returns:
            The registry instance for chained registrations.

        Raises:
            PlayerAlreadyExistsError:
                An identifier is already registered or occurs multiple times.
            PlayerDestroyedError:
                A supplied player has already been destroyed.
            TypeError:
                A supplied player identifier is not an integer.
        """

        new_players: tuple[MediaPlayer, ...] = tuple(players)

        if not new_players:
            return self

        validated_players: list[tuple[int, MediaPlayer]] = []
        known_identifiers: set[int] = set(self._players)

        for player in new_players:
            player_identifier: int = self._validate_identifier(player.identifier)

            if player.destroyed:
                raise PlayerDestroyedError

            if player_identifier in known_identifiers:
                raise PlayerAlreadyExistsError(player_identifier=player_identifier)

            known_identifiers.add(player_identifier)
            validated_players.append(
                (
                    player_identifier,
                    player,
                )
            )

        self._players.update(validated_players)
        return self

    def get(self, player_identifier: int) -> MediaPlayer:
        """Return a registered player by identifier.

        Args:
            player_identifier:
                The numeric identifier of the player.

        Returns:
            The matching registered media player.

        Raises:
            PlayerNotFoundError:
                No player uses the supplied identifier.
            TypeError:
                The player identifier is not an integer.
        """

        normalized_identifier: int = self._validate_identifier(player_identifier)

        try:
            return self._players[normalized_identifier]
        except KeyError as exception:
            raise PlayerNotFoundError(player_identifier=normalized_identifier) from exception

    def remove(self, player_identifier: int) -> MediaPlayer:
        """Remove and return a player without destroying it.

        The caller becomes responsible for destroying the removed player.

        Args:
            player_identifier:
                The numeric identifier of the player to remove.

        Returns:
            The removed media player.

        Raises:
            PlayerNotFoundError:
                No player uses the supplied identifier.
            TypeError:
                The player identifier is not an integer.
        """

        normalized_identifier: int = self._validate_identifier(player_identifier)

        try:
            return self._players.pop(normalized_identifier)
        except KeyError as exception:
            raise PlayerNotFoundError(player_identifier=normalized_identifier) from exception

    async def destroy(self, player_identifier: int) -> None:
        """Remove and destroy one registered media player.

        The player is removed before destruction begins so it cannot be
        retrieved while cleanup is in progress.

        Args:
            player_identifier:
                The numeric identifier of the player to destroy.

        Raises:
            PlayerNotFoundError:
                No player uses the supplied identifier.
            TypeError:
                The player identifier is not an integer.
            Exception:
                Player-specific cleanup failed.
        """

        player: MediaPlayer = self.remove(player_identifier)
        await player.destroy()

    async def destroy_all(self) -> None:
        """Remove and destroy every registered media player.

        Every player receives a destruction request even when another player
        fails during cleanup. Players are destroyed in reverse registration
        order.

        Raises:
            ExceptionGroup:
                One or more players failed during destruction.
        """

        players: tuple[MediaPlayer, ...] = tuple(reversed(self._players.values()))
        self._players.clear()
        exceptions: list[Exception] = []

        for player in players:
            try:
                await player.destroy()
            except Exception as exception:
                exceptions.append(exception)

        if exceptions:
            raise ExceptionGroup(
                "One or more media players failed to destroy.",
                exceptions
            )

    def clear(self) -> tuple[MediaPlayer, ...]:
        """Remove and return every player without destroying them.

        The caller becomes responsible for destroying the removed players.

        Returns:
            The removed players in their previous registration order.
        """

        removed_players: tuple[MediaPlayer, ...] = tuple(self._players.values())
        self._players.clear()

        return removed_players

    def __contains__(self, player_identifier: object) -> bool:
        """Return whether a player identifier is registered.

        Args:
            player_identifier:
                The possible numeric player identifier.

        Returns:
            ``True`` when a matching player is registered.
        """

        if (

            isinstance(player_identifier, bool)
            or not isinstance(player_identifier, int)
        ):
            return False

        return player_identifier in self._players

    def __getitem__(self, player_identifier: int) -> MediaPlayer:
        """Return a registered player by identifier.

        Args:
            player_identifier:
                The numeric identifier of the player.

        Returns:
            The matching registered media player.

        Raises:
            PlayerNotFoundError:
                No player uses the supplied identifier.
            TypeError:
                The player identifier is not an integer.
        """

        return self.get(player_identifier)

    def __iter__(self) -> Iterator[MediaPlayer]:
        """Iterate over registered media players.

        Returns:
            An iterator following player registration order.
        """

        return iter(self._players.values())

    def __len__(self) -> int:
        """Return the number of registered players.

        Returns:
            The current registry size.
        """

        return len(self._players)

    def __bool__(self) -> bool:
        """Return whether the registry contains any players.

        Returns:
            ``True`` when at least one player is registered.
        """

        return bool(self._players)

    @staticmethod
    def _validate_identifier(player_identifier: int) -> int:
        """Validate a media player identifier.

        Args:
            player_identifier:
                The numeric identifier to validate.

        Returns:
            The validated player identifier.

        Raises:
            TypeError:
                The value is not an integer or is a boolean.
        """

        if isinstance(player_identifier, bool) or not isinstance(
            player_identifier,
            int
        ):
            raise TypeError("The media player identifier must be an integer.")

        return player_identifier

__all__: tuple[str, ...] = ("PlayerRegistry",)
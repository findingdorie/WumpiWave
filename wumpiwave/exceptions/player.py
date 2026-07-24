"""Media player exceptions raised throughout WumpiWave.

This module defines errors related to player registration, player lookup,
invalid playback states, destroyed players, and unavailable current tracks.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from ..models import PlayerState
from .base import WumpiWaveError


class PlayerError(WumpiWaveError):
    """Represent the base exception for media player errors.

    Attributes:
        None

    Methods:
        None
    """

    __slots__ = ()

class PlayerAlreadyExistsError(PlayerError):
    """Represent an attempt to create an existing media player.

    Attributes:
        player_identifier:
            The unique identifier already assigned to an existing player.

    Methods:
        __init__.py:
            Initialize the exception with the duplicate player identifier.
    """

    __slots__ = ("player_identifier",)

    player_identifier: int

    def __init__(self, player_identifier: int) -> None:
        """Initialize a player-already-exists error.

        Args:
            player_identifier:
                The unique identifier already assigned to an existing player.

        Raises:
            ValueError:
                The player identifier is not greater than zero.
        """

        if player_identifier <= 0:
            raise ValueError("The player identifier must be greater than zero.")

        self.player_identifier = player_identifier

        super().__init__(
            f"A media player with identifier {self.player_identifier} already exists."
        )

class PlayerNotFoundError(PlayerError):
    """Represent a media player that could not be found.

    Attributes:
        player_identifier:
            The unique identifier of the requested player.

    Methods:
        __init__.py:
            Initialize the exception with the missing player identifier.
    """

    __slots__ = ("player_identifier",)

    player_identifier: int

    def __init__(self, player_identifier: int) -> None:
        """Initialize a player-not-found error.

        Args:
            player_identifier:
                The unique identifier of the player that could not be found.

        Raises:
            ValueError:
                The player identifier is not greater than zero.
        """

        if player_identifier <= 0:
            raise ValueError("The player identifier must be greater than zero.")

        self.player_identifier = player_identifier

        super().__init__(
            f"No media player with identifier {player_identifier} was found."
        )

class InvalidPlayerStateError(PlayerError):
    """Represent an operation unavailable in the current player state.

    Attributes:
        operation:
            The player operation that could not be performed.
        current_state:
            The player state active when the operation was attempted.
        allowed_states:
            The player states in which the operation is permitted.

    Methods:
        __init__.py:
            Initialize the exception with the operation and state information.
    """

    __slots__ = (
        "allowed_states",
        "current_state",
        "operation"
    )

    operation: str
    current_state: PlayerState
    allowed_states: tuple[PlayerState, ...]

    def __init__(self, operation: str, current_state: PlayerState, allowed_states: tuple[PlayerState, ...]) -> None:
        """Initialize an invalid player state error.

        Args:
            operation:
                The player operation that could not be performed.
            current_state:
                The player state active when the operation was attempted.
            allowed_states:
                The player states in which the operation is permitted.

        Raises:
            ValueError:
                The operation name or allowed state collection is empty.
        """

        normalized_operation: str = operation.strip()

        if not normalized_operation:
            raise ValueError("The player operation cannot be empty.")

        if not allowed_states:
            raise ValueError("At least one allowed player state is required.")

        self.operation = normalized_operation
        self.current_state = current_state
        self.allowed_states = allowed_states

        allowed_state_names: str = ", ".join(
            state.value for state in allowed_states
        )

        super().__init__(
            f"Player operation {normalized_operation!r} is unavailable while "
            f"the player is {current_state.value!r}. Allowed states: "
            f"{allowed_state_names}."
        )

class PlayerDestroyedError(PlayerError):
    """Represent an operation attempted on a destroyed media player.

    Attributes:
        None

    Methods:
        __init__.py:
            Initialize the exception with a descriptive error message.
    """

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize a player-destroyed error."""

        super().__init__("The media player has been destroyed and cannot be used again.")

class NoCurrentTrackError(PlayerError):
    """Represent an operation requiring a current queue entry.

    This exception is raised when an operation such as pause, seek, or restart
    requires an active track, but the media player has no current queue entry.

    Attributes:
        None

    Methods:
        __init__.py:
            Initialize the exception with a descriptive error message.
    """

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize a missing-current-track error."""

        super().__init__("The media player does not have a current track.")

__all__: tuple[str, ...] = (
    "InvalidPlayerStateError",
    "NoCurrentTrackError",
    "PlayerAlreadyExistsError",
    "PlayerDestroyedError",
    "PlayerError",
    "PlayerNotFoundError",
)
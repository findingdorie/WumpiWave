"""
Playback event models used throughout WumpiWave.

This module provides source-independent event data emitted during track
playback, queue exhaustion, player state changes, and player destruction.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from ..enums import PlayerState, TrackEndReason
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4
from .queue import QueueEntry

@dataclass(frozen=True, slots=True, kw_only=True)
class PlaybackEvent:
    """
    Represents the base model for every playback event.

    Each event receives a unique identifier and timezone-aware creation
    timestamp. Specialized playback events inherit these shared values.

    Attributes:
        - identifier:
            The unique identifier assigned to the event.
        - created_at:
            The timezone-aware UTC date and time at which the event was created.

    Methods:
        None
    """

    identifier: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

@dataclass(frozen=True, slots=True)
class TrackEvent(PlaybackEvent):
    """
    Represents the base model for events associated with a queue entry.

    Attributes:
        - entry:
            The queue entry associated with the playback event.
        - identifier:
            The unique identifier assigned to the event.
        - created_at:
            The timezone-aware UTC date and time at which the event was created.

    Methods:
        None
    """

    entry: QueueEntry

@dataclass(frozen=True, slots=True)
class TrackStartEvent(TrackEvent):
    """
    Represents the beginning of playback for a queue entry.

    Attributes:
        - entry:
            The queue entry whose playback has started.
        - identifier:
            The unique identifier assigned to the event.
        - created_at:
            The timezone-aware UTC date and time at which the event was created.

    Methods:
        None
    """

@dataclass(frozen=True, slots=True)
class TrackEndEvent(TrackEvent):
    """
    Represents the end of playback for a queue entry.

    The event stores the reason playback ended and optionally includes the
    exception responsible for an unsuccessful playback operation.

    Attributes:
        - entry:
            The queue entry whose playback has ended.
        - reason:
            The reason why playback of the queue entry ended.
        - exception:
            The exception that interrupted playback when the reason is
            ``TrackEndReason.ERROR``.
        - identifier:
            The unique identifier assigned to the event.
        - created_at:
            The timezone-aware UTC date and time at which the event was created.

    Methods:
        __post_init__:
            Validates the relationship between the end reason and exception.
    """

    reason: TrackEndReason
    exception: Exception | None = None

    def __post_init(self) -> None:
        """
        Validate the track end event data.

        Raises:
            ValueError:
                An error reason has no exception, or an exception is supplied
                for a non-error reason.
        """

        if self.reason is TrackEndReason.ERROR and self.exception is None:
            raise ValueError("An exception is required when the track end reason is error.")

        if self.reason is not TrackEndReason.ERROR and self.exception is not None:
            raise ValueError("An exception can only be supplied for an error end reason.")

@dataclass(frozen=True, slots=True)
class QueueEmptyEvent(PlaybackEvent):
    """
    Represents a playback queue becoming empty.

    Attributes:
        - previous_entry:
            The queue entry that finished immediately before the queue became
            empty, when available.
        - identifier:
            The unique identifier assigned to the event.
        - created_at:
            The timezone-aware UTC date and time at which the event was created.

    Methods:
        None
    """

    previous_entry: QueueEntry | None = None


@dataclass(frozen=True, slots=True)
class PlayerStateChangeEvent(PlaybackEvent):
    """
    Represents a transition between two player states.

    Attributes:
        - previous_state:
            The player state active before the transition.
        - current_state:
            The player state active after the transition.
        - identifier:
            The unique identifier assigned to the event.
        - created_at:
            The timezone-aware UTC date and time at which the event was created.

    Methods:
        __post_init__:
            Validates that the previous and current states differ.
    """

    previous_state: PlayerState
    current_state: PlayerState

    def __post_init__(self) -> None:
        """
        Validate the player state transition.

        Raises:
            ValueError:
                The previous and current player states are identical.
        """

        if self.previous_state is self.current_state:
            raise ValueError("A player state change requires two different states.")

@dataclass(frozen=True, slots=True)
class PlayerDestroyEvent(PlaybackEvent):
    """
    Represents the permanent destruction of a media player.

    Attributes:
        - identifier:
            The unique identifier assigned to the event.
        - created_at:
            The timezone-aware UTC date and time at which the event was created.

    Methods:
        None
    """

__all__: tuple[str, ...] = (
    "PlaybackEvent",
    "PlayerDestroyEvent",
    "PlayerStateChangeEvent",
    "QueueEmptyEvent",
    "TrackEndEvent",
    "TrackEvent",
    "TrackStartEvent",
)
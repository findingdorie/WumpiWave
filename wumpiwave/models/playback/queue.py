"""
Queue entry models used throughout WumpiWave.

This module provides the source-independent representation of tracks stored
inside a media player's playback queue.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from ..media import MediaTrack
from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import isfinite
from uuid import UUID, uuid4

@dataclass(frozen=True, slots=True)
class QueueEntry:
    """
    Represents a media track stored inside a playback queue.

    A queue entry separates playback-specific information from the underlying
    media track. This allows the same track to appear multiple times with
    different requesters, start positions, and request timestamps.

    Attributes:
        - identifier:
            The unique identifier assigned to the queue entry.
        - track:
            The media track associated with the queue entry.
        - requester_id:
            The Discord user identifier of the requester, when available.
        - requested_at:
            The timezone-aware UTC date and time at which the track was queued.
        - start_position:
            The playback position in seconds from which the track should begin.

    Methods:
        __post_init__:
            Validates the requester identifier, request timestamp, and start
            position.
        has_requester:
            Indicates whether a requester identifier is associated with the
            queue entry.
        remaining_duration:
            Returns the estimated remaining track duration in seconds.
    """

    track: MediaTrack
    identifier: UUID = field(default_factory=uuid4)
    requester_id: int | None = None
    requested_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    start_position: float = 0.0

    def __post_init__(self) -> None:
        """
        Validate the queue entry data.

        Raises:
            ValueError:
                The requester identifier is not positive, the request timestamp
                lacks timezone information, or the start position is invalid.
        """

        if self.requester_id is not None and self.requested_at <= 0:
            raise ValueError("The requester identifier must be greater than zero.")

        if self.requested_at.tzinfo is None:
            raise ValueError("The requested timestamp must contain timezone information.")

        if not isfinite(self.start_position):
            raise ValueError("The start position must be finite.")

        if self.start_position < 0.0:
            raise ValueError("The start position cannot be negative.")

        if (
            self.track.duration is not None
            and self.start_position > self.track.duration
        ):
            raise ValueError("The start position cannot exceed the track duration.")

    @property
    def has_requester(self) -> bool:
        """
        Return whether the queue entry has an associated requester.

        Returns:
            ``True`` when a requester identifier is available, otherwise
            ``False``.
        """

        return self.requester_id is not None

    @property
    def remaining_duration(self) -> float | None:
        """
        Return the estimated remaining track duration in seconds.

        Returns:
            The remaining duration after subtracting the start position, or
            ``None`` when the track duration is unknown.
        """

        if self.track.duration is None:
            return None

        return max(0.0, self.track.duration - self.start_position)

__all__: tuple[str, ...] = (
    "QueueEntry",
)
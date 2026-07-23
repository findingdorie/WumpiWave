"""Playback queue exceptions raised throughout WumpiWave.

This module defines errors related to empty queues, invalid queue positions,
and missing queue entries.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from uuid import UUID

from .base import WumpiWaveError


class QueueError(WumpiWaveError):
    """Represents the base exception for playback queue errors.

    Attributes:
        None

    Methods:
        None
    """

    __slots__ = ()

class QueueEmptyError(QueueError):
    """Represent an operation performed on an empty playback queue.

    This exception is raised when an operation requires at least one queue
    entry, but the playback queue does not contain any entries.

    Attributes:
        None

    Methods:
        __init__:
            Initialize the exception with a descriptive error message.
    """

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize an empty playback queue error."""

        super().__init__("The playback queue is empty.")

class QueueIndexOutOfRangeError(QueueError):
    """Represent an invalid position inside a playback queue.

    Attributes:
        index:
            The queue index requested by the caller.
        queue_size:
            The number of entries available when the operation was attempted.

    Methods:
        __init__:
            Initialize the exception with the invalid index and queue size.
    """

    __slots__ = (
        "index",
        "queue_size"
    )

    index: int
    queue_size: int

    def __init__(self, index: int, queue_size: int) -> None:
        """Initialize a queue index error.

        Args:
            index:
                The invalid queue index requested by the caller.
            queue_size:
                The number of entries currently available in the queue.
        """

        self.index = index
        self.queue_size = queue_size

        super().__init__(
            f"Queue index {index} is out of range for a queue containing "
            f"{queue_size} entries."
        )

class QueueEntryNotFoundError(QueueError):
    """Represent a queue entry that could not be found.

    Attributes:
        entry_identifier:
            The unique identifier of the requested queue entry.

    Methods:
        __init__:
            Initialize the exception with the missing entry identifier.
    """

    __slots__ = ("entry_identifier",)

    entry_identifier: UUID

    def __init__(self, entry_identifier: UUID) -> None:
        """Initialize a queue entry lookup error.

        Args:
            entry_identifier:
                The unique identifier of the queue entry that could not be
                found.
        """

        self.entry_identifier = entry_identifier

        super().__init__(
            f"No queue entry with identifier {entry_identifier!s} was found."
        )

__all__: tuple[str, ...] = (
    "QueueEmptyError",
    "QueueEntryNotFoundError",
    "QueueError",
    "QueueIndexOutOfRangeError",
)
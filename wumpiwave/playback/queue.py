"""Playback queue implementation used by WumpiWave.

This module provides ordered queue storage, entry creation, lookup, removal,
movement, shuffling, and inspection for normalized media tracks.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Iterator
from typing import Self
from uuid import UUID

from wumpiwave.models import QueueEntry
from ..exceptions import (
    QueueEmptyError,
    QueueEntryNotFoundError,
    QueueError,
    QueueIndexOutOfRangeError,
)
from ..models import MediaTrack, QueueEntry

class PlaybackQueue:
    """Manage ordered media entries awaiting playback.

    Queue entries retain their registration order unless they are moved,
    removed, or shuffled explicitly. Every entry is identified by a unique
    UUID, allowing callers to safely reference entries even when their indexes
    change.

    Attributes:
        entries:
            An immutable snapshot of all queued entries.
        first:
            The first queued entry, when available.
        last:
            The last queued entry, when available.
        size:
            The number of queued entries.
        is_empty:
            Whether the queue contains no entries.

    Methods:
        add:
            Create and append a queue entry for a media track.
        add_entry:
            Append an existing queue entry.
        extend:
            Append multiple existing queue entries.
        get:
            Return the entry at a queue index.
        find:
            Return an entry by its unique identifier.
        index:
            Return the current index of an entry identifier.
        peek:
            Inspect an entry without removing it.
        pop:
            Remove and return an entry by index.
        remove_entry:
            Remove and return an entry by identifier.
        replace:
            Replace an entry at a queue index.
        move:
            Move an entry to another queue index.
        swap:
            Exchange the positions of two queue entries.
        shuffle:
            Randomize the queue order.
        clear:
            Remove and return every queued entry.
        copy:
            Create an independent queue containing the same entries.
        __contains__:
            Determine whether an entry or identifier exists in the queue.
        __getitem__:
            Return an entry or immutable slice by index.
        __iter__:
            Iterate over a snapshot of queued entries.
        __reversed__:
            Iterate over a reversed snapshot of queued entries.
        __len__:
            Return the number of queued entries.
        __bool__:
            Return whether the queue contains any entries.
    """

    __slots__ = ("_entries",)

    _entries: list[QueueEntry]

    def __init__(self, entries: Iterable[QueueEntry] = ()) -> None:
        """Initialize a playback queue.

        Args:
            entries:
                Existing queue entries added during initialization.

        Raises:
            QueueError:
                Multiple entries use the same unique identifier.
        """

        self._entries = []
        self.extend(entries)

    @property
    def entries(self) -> tuple[QueueEntry, ...]:
        """Return an immutable snapshot of queued entries.

        Returns:
            The entries in their current playback order.
        """

        return tuple(self._entries)

    @property
    def first(self) -> QueueEntry | None:
        """Return the first queued entry.

        Returns:
            The first entry, or ``None`` when the queue is empty.
        """

        if not self._entries:
            return None

        return self._entries[0]

    @property
    def last(self) -> QueueEntry | None:
        """Return the last queued entry.

        Returns:
            The last entry, or ``None`` when the queue is empty.
        """

        if not self._entries:
            return None

        return self._entries[-1]

    @property
    def size(self) -> int:
        """Return the number of queued entries.

        Returns:
            The current queue size.
        """

        return len(self._entries)

    @property
    def is_empty(self) -> bool:
        """Return whether the playback queue is empty.

        Returns:
            ``True`` when the queue contains no entries.
        """

        return not self._entries

    def add(
            self,
            track: MediaTrack,
            *,
            requester_id: int | None = None,
            start_position: float = 0.0
    ) -> QueueEntry:
        """Create and append a queue entry for a media track.

        Args:
            track:
                The normalized media track to enqueue.
            requester_id:
                The optional identifier of the user requesting the track.
            start_position:
                The initial playback position in seconds.

        Returns:
            The newly created and appended queue entry.

        Raises:
            ValueError:
                The requester identifier or start position is invalid.
        """

        entry = QueueEntry(
            track=track,
            requester_id=requester_id,
            start_position=start_position
        )
        self._entries.append(entry)

        return entry

    def add_entry(self, entry: QueueEntry) -> Self:
        """Append an existing queue entry.

        Args:
            entry:
                The existing queue entry to append.

        Returns:
            The queue instance for chained operations.

        Raises:
            QueueError:
                The entry identifier already exists in the queue.
        """

        self._ensure_identifier_available(entry.identifier)
        self._entries.append(entry)

        return self

    def extend(self, entries: Iterable[QueueEntry]) -> Self:
        """Append multiple existing queue entries.

        Validation occurs before the queue is modified, preventing partial
        insertion when duplicate identifiers are supplied.

        Args:
            entries:
                The queue entries to append.

        Returns:
            The queue instance for chained operations.

        Raises:
            QueueError:
                An identifier already exists or occurs multiple times in the
                supplied entries.
        """

        new_entries: tuple[QueueEntry, ...] = tuple(entries)

        if not new_entries:
            return self

        existing_identifiers: set[UUID] = {
            entry.identifier for entry in self._entries
        }
        new_identifiers: set[UUID] = set()

        for entry in new_entries:
            if (
                entry.identifier in existing_identifiers
                or entry.identifier in new_identifiers
            ):
                raise QueueError(
                    f"Queue entry identifier {entry.identifier!s} "
                    "is already present."
                )

            new_identifiers.add(entry.identifier)

        self._entries.extend(new_entries)
        return self

    def get(self, index: int) -> QueueEntry:
        """Return an entry by its queue index.

        Negative indexes follow normal Python indexing behavior.

        Args:
            index:
                The queue index to retrieve.

        Returns:
            The entry stored at the normalized index.

        Raises:
            QueueIndexOutOfRangeError:
                The supplied index is outside the queue.
        """

        normalized_index: int = self._normalize_index(index)
        return self._entries[normalized_index]

    def find(self, entry_identifier: UUID) -> QueueEntry:
        """Return an entry by its unique identifier.

        Args:
            entry_identifier:
                The UUID of the queue entry to locate.

        Returns:
            The matching queue entry.

        Raises:
            QueueEntryNotFoundError:
                No queued entry uses the supplied identifier.
        """

        return self._entries[self.index(entry_identifier)]

    def index(self, entry_identifier: UUID) -> int:
        """Return the current index of a queue entry.

        Args:
            entry_identifier:
                The UUID of the queue entry to locate.

        Returns:
            The zero-based queue index of the matching entry.

        Raises:
            QueueEntryNotFoundError:
                No queued entry uses the supplied identifier.
        """

        for entry_index, entry in enumerate(self._entries):
            if entry.identifier == entry_identifier:
                return entry_index

        raise QueueEntryNotFoundError(entry_identifier=entry_identifier)

    def peek(self, index: int = 0) -> QueueEntry:
        """Inspect an entry without removing it.

        Args:
            index:
                The queue index to inspect.

        Returns:
            The queued entry at the supplied index.

        Raises:
            QueueEmptyError:
                The playback queue is empty.
            QueueIndexOutOfRangeError:
                The supplied index is outside the queue.
        """

        self._ensure_not_empty()
        return self.get(index)

    def pop(self, index: int = 0) -> QueueEntry:
        """Remove and return an entry by index.

        Args:
            index:
                The queue index to remove.

        Returns:
            The removed queue entry.

        Raises:
            QueueEmptyError:
                The playback queue is empty.
            QueueIndexOutOfRangeError:
                The supplied index is outside the queue.
        """

        self._ensure_not_empty()

        normalized_index: int = self._normalize_index(index)
        return self._entries.pop(normalized_index)

    def remove_entry(self, entry_identifier: UUID) -> QueueEntry:
        """Remove and return an entry by its identifier.

        Args:
            entry_identifier:
                The UUID of the queue entry to remove.

        Returns:
            The removed queue entry.

        Raises:
            QueueEntryNotFoundError:
                No queued entry uses the supplied identifier.
        """

        return self._entries.pop(self.index(entry_identifier))

    def replace(self, index: int, entry: QueueEntry) -> QueueEntry:
        """Replace an entry at a queue index.

        The replacement may reuse the identifier of the entry being replaced,
        but it cannot use the identifier of another queued entry.

        Args:
            index:
                The index of the entry to replace.
            entry:
                The replacement queue entry.

        Returns:
            The queue entry that was replaced.

        Raises:
            QueueError:
                The replacement identifier belongs to another queued entry.
            QueueIndexOutOfRangeError:
                The supplied index is outside the queue.
        """

        normalized_index: int = self._normalize_index(index)
        current_entry: QueueEntry = self._entries[normalized_index]

        if entry.identifier != current_entry.identifier:
            self._ensure_identifier_available(entry.identifier)

        self._entries[normalized_index] = entry
        return current_entry

    def move(self, source_index: int, destination_index: int) -> Self:
        """Move an entry to another queue index.

        The destination represents the entry's position in the final queue.

        Args:
            source_index:
                The current index of the entry to move.
            destination_index:
                The desired final index of the entry.

        Returns:
            The queue instance for chained operations.

        Raises:
            QueueEmptyError:
                The playback queue is empty.
            QueueIndexOutOfRangeError:
                Either supplied index is outside the queue.
        """

        self._ensure_not_empty()

        normalized_source: int = self._normalize_index(source_index)
        normalized_destination: int = self._normalize_index(destination_index)

        if normalized_source == normalized_destination:
            return self

        entry: QueueEntry = self._entries.pop(normalized_source)
        self._entries.insert(normalized_destination, entry)

        return self

    def swap(self, first_index: int, second_index: int) -> Self:
        """Exchange the positions of two queue entries.

        Args:
            first_index:
                The index of the first queue entry.
            second_index:
                The index of the second queue entry.

        Returns:
            The queue instance for chained operations.

        Raises:
            QueueEmptyError:
                The playback queue is empty.
            QueueIndexOutOfRangeError:
                Either supplied index is outside the queue.
        """

        self._ensure_not_empty()

        normalized_first: int = self.normalize_index(first_index)
        normalized_second: int = self._normalize_index(second_index)

        if normalized_first == normalized_second:
            return self

        self._entries[normalized_first], self._entries[normalized_second] = (
            self._entries[normalized_second],
            self._entries[normalized_first]
        )

        return self

    def shuffle(self, *, randomizer: random.Random | None = None) -> Self:
        """Randomize the playback queue order.

        Args:
            randomizer:
                An optional random number generator used for deterministic
                testing or custom randomization.

        Returns:
            The queue instance for chained operations.
        """

        if len(self._entries) < 2:
            return self

        if randomizer is None:
            random.shuffle(self._entries)
        else:
            randomizer.shuffle(self._entries)

        return self

    def clear(self) -> tuple[QueueEntry, ...]:
        """Remove and return every queue entry.

        Returns:
            The removed entries in their previous playback order.
        """

        removed_entries: tuple[QueueEntry, ...] = tuple(self._entries)
        self._entries.clear()

        return removed_entries

    def copy(self) -> PlaybackQueue:
        """Create an independent copy of the playback queue.

        Queue entries are immutable and are therefore shared safely between the
        original and copied queue.

        Returns:
            A new queue containing the same entries and order.
        """

        return PlaybackQueue(self._entries)

    def __contains__(self, value: object) -> bool:
        """Return whether an entry or identifier exists in the queue.

        Args:
            value:
                A queue entry or UUID to inspect.

        Returns:
            ``True`` when the associated identifier exists in the queue.
        """

        if isinstance(value, QueueEntry):
            entry_identifier: UUID = value.identifier
        elif isinstance(value, UUID):
            entry_identifier = value
        else:
            return False

        return any(entry.identifier == entry_identifier for entry in self._entries)

    def __getitem__(self, index: int | slice) -> QueueEntry | tuple[QueueEntry, ...]:
        """Return an entry or immutable queue slice.

        Args:
            index:
                The integer index or slice to retrieve.

        Returns:
            A queue entry for integer indexes or an immutable tuple for slices.

        Raises:
            QueueIndexOutOfRangeError:
                An integer index is outside the queue.
        """

        if isinstance(index, slice):
            return tuple(self._entries[index])

        return self.get(index)

    def __iter__(self) -> Iterator[QueueEntry]:
        """Iterate over a snapshot of queue entries.

        Returns:
            An iterator following the current playback order.
        """

        return iter(tuple(self._entries))

    def __reversed__(self) -> Iterator[QueueEntry]:
        """Iterate over a reversed snapshot of queue entries.

        Returns:
            An iterator following the reverse playback order.
        """

        return iter(tuple(reversed(self._entries)))

    def __len__(self) -> int:
        """Return the number of queued entries.

        Returns:
            The current playback queue size.
        """

        return len(self._entries)

    def __bool__(self) -> bool:
        """Return whether the queue contains any entries.

        Returns:
            ``True`` when at least one entry is queued.
        """

        return bool(self._entries)

    def _ensure_identifier_available(self, entry_identifier: UUID) -> None:
        """Ensure that an entry identifier is not already queued.

        Args:
            entry_identifier:
                The UUID that should be available.

        Raises:
            QueueError:
                The supplied identifier already exists in the queue.
        """

        if entry_identifier in self:
            raise QueueError(
                f"Queue entry identifier {entry_identifier!s} "
                "is already present."
            )

    def _ensure_not_empty(self) -> None:
        """Ensure that the playback queue contains an entry.

        Raises:
            QueueEmptyError:
                The playback queue is empty.
        """

        if not self._entries:
            raise QueueError

    def _normalize_index(self, index: int) -> int:
        """Normalize and validate a queue index.

        Args:
            index:
                The positive or negative queue index to normalize.

        Returns:
            The equivalent non-negative queue index.

        Raises:
            QueueIndexOutOfRangeError:
                The index is outside the current queue.
        """

        queue_size: int = len(self._entries)
        normalized_index: int = index

        if normalized_index < 0:
            normalized_index += queue_size

        if not 0 <= normalized_index < queue_size:
            raise QueueIndexOutOfRangeError(
                index=index,
                queue_size=queue_size
            )

        return normalized_index

__all__: tuple[str, ...] = ("PlaybackQueue",)

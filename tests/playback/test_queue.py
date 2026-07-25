"""Tests for the WumpiWave playback queue."""

from __future__ import annotations

import random
import unittest
from uuid import UUID

from wumpiwave.exceptions import (
    QueueEmptyError,
    QueueEntryNotFoundError,
    QueueError,
    QueueIndexOutOfRangeError,
)
from wumpiwave.models import MediaSource, MediaTrack, QueueEntry
from wumpiwave.playback import PlaybackQueue

class PlaybackQueueTestCase(unittest.TestCase):
    """Test queue storage, ordering, lookup, and mutation behavior."""

    def setUp(self) -> None:
        """Create resuable media tracks for each test."""

        self.first_track = MediaTrack(
            identifier="first",
            source=MediaSource.YOUTUBE,
            title="First track",
            url="https://www.youtube.com/watch?v=first"
        )

        self.second_track = MediaTrack(
            identifier="second",
            source=MediaSource.YOUTUBE,
            title="Second track",
            url="https://www.youtube.com/watch?v=second"
        )

        self.third_track = MediaTrack(
            identifier="third",
            source=MediaSource.SPOTIFY,
            title="Third track",
            url="https://open.spotify.com/track/third"
        )

    def test_add_creates_and_appends_entry(self) -> None:
        """Verify that adding a track creates a queue entry."""

        queue = PlaybackQueue()
        entry = queue.add(
            self.first_track,
            requester_id=123,
            start_position=15.0
        )

        self.assertEqual(len(queue), 1)
        self.assertIs(queue.first, entry)
        self.assertIs(queue.last, entry)
        self.assertIs(entry.track, self.first_track)
        self.assertEqual(entry.requester_id, 123)
        self.assertEqual(entry.start_position, 15.0)

    def test_add_entry_rejects_duplicate_identifier(self) -> None:
        """Verify that duplicate queue identifiers are rejected."""

        entry = QueueEntry(track=self.first_track)
        duplicate = QueueEntry(
            track=self.second_track,
            identifier=entry.identifier
        )
        queue = PlaybackQueue((entry,))

        with self.assertRaises(QueueError):
            queue.add_entry(duplicate)

        self.assertEqual(queue.entries, (entry,))

    def test_extend_is_atomic_when_identifier_is_duplicated(self) -> None:
        """Verify that failed extension does not modify the queue."""

        existing_entry = QueueEntry(track=self.first_track)
        valid_entry = QueueEntry(track=self.second_track)
        duplicate_entry = QueueEntry(
            track=self.third_track,
            identifier=existing_entry.identifier
        )
        queue = PlaybackQueue((existing_entry,))

        with self.assertRaises(QueueError):
            queue.extend(
                (
                    valid_entry,
                    duplicate_entry
                )
            )

        self.assertEqual(queue.entries, (existing_entry,))

    def test_get_supports_negative_indexes(self) -> None:
        """Verify that queue lookup supports negative indexes."""

        first_entry = QueueEntry(track=self.first_track)
        second_entry = QueueEntry(track=self.second_track)
        queue = PlaybackQueue(
            (
                first_entry,
                second_entry
            )
        )

        self.assertIs(queue.get(0), first_entry)
        self.assertIs(queue.get(-1), second_entry)

    def test_get_rejects_out_of_range_index(self) -> None:
        """Verify that invalid queue indexes raise the queue exception."""

        queue = PlaybackQueue()

        with self.assertRaises(QueueIndexOutOfRangeError):
            queue.get(0)

    def test_find_and_index_use_entry_identifier(self) -> None:
        """Verify that entries can be found through their identifiers."""

        entry = QueueEntry(track=self.first_track)
        queue = PlaybackQueue((entry,))

        self.assertIs(queue.find(entry.identifier), entry)
        self.assertEqual(queue.index(entry.identifier), 0)

    def test_find_rejects_unknown_identifier(self) -> None:
        """Verify that unknown identifiers raise the lookup exception."""

        queue = PlaybackQueue()

        with self.assertRaises(QueueEntryNotFoundError):
            queue.find(UUID("00000000-0000-0000-0000-000000000000"))

    def test_peek_does_not_remove_entry(self) -> None:
        """Verify that peeking leaves the queue unchanged."""

        entry = QueueEntry(track=self.first_track)
        queue = PlaybackQueue((entry,))

        result = queue.peek()

        self.assertIs(result, entry)
        self.assertEqual(queue.entries, (entry,))

    def test_peek_rejects_empty_queue(self) -> None:
        """Verify that peeking into an empty queue fails."""

        first_entry = QueueEntry(track=self.first_track)
        second_entry = QueueEntry(track=self.second_track)
        queue = PlaybackQueue(
            (
                first_entry,
                second_entry
            )
        )

        removed_entry = queue.pop()

        self.assertIs(removed_entry, first_entry)
        self.assertEqual(queue.entries, (second_entry,))

    def test_remove_entry_uses_identifier(self) -> None:
        """Verify that an entry can be removed by identifier."""

        entry = QueueEntry(track=self.first_track)
        queue = PlaybackQueue((entry,))

        removed_entry = queue.remove_entry(entry.identifier)

        self.assertIs(removed_entry, entry)
        self.assertTrue(queue.is_empty)

    def test_replace_returns_previous_entry(self) -> None:
        """Verify that replacing an entry returns the old entry."""

        previous_entry = QueueEntry(track=self.first_track)
        replacement_entry = QueueEntry(track=self.second_track)
        queue = PlaybackQueue((previous_entry,))

        replaced_entry = queue.replace(0, replacement_entry)

        self.assertIs(replaced_entry, previous_entry)
        self.assertEqual(queue.entries, (replacement_entry,))

    def test_move_changes_entry_order(self) -> None:
        """Verify that moving an entry changes its final position."""

        first_entry = QueueEntry(track=self.first_track)
        second_entry = QueueEntry(track=self.second_track)
        third_entry = QueueEntry(track=self.third_track)
        queue = PlaybackQueue(
            (
                first_entry,
                second_entry,
                third_entry
            )
        )

        queue.move(0, 2)

        self.assertEqual(
            queue.entries,
            (
                second_entry,
                third_entry,
                first_entry
            )
        )

    def test_swap_exchanges_two_entries(self) -> None:
        """Verify that swapping exchanges queue positions."""

        first_entry = QueueEntry(track=self.first_track)
        second_entry = QueueEntry(track=self.second_track)
        queue = PlaybackQueue(
            (
                first_entry,
                second_entry
            )
        )

        queue.swap(0, 1)

        self.assertEqual(
            queue.entries,
            (
                second_entry,
                first_entry
            )
        )

    def test_shuffle_accepts_deterministic_randomizer(self) -> None:
        """Verify that a supplied randomizer controls queue shuffling."""

        entries = (
            QueueEntry(track=self.first_track),
            QueueEntry(track=self.second_track),
            QueueEntry(track=self.third_track)
        )
        first_queue = PlaybackQueue(entries)
        second_queue = PlaybackQueue(entries)

        first_queue.shuffle(randomizer=random.Random(123))
        second_queue.shuffle(randomizer=random.Random(123))

        self.assertEqual(first_queue.entries, second_queue.entries)

    def test_clear_returns_previous_entries(self) -> None:
        """Verify that clearing returns the previous queue contents."""

        entries = (
            QueueEntry(track=self.first_track),
            QueueEntry(track=self.second_track)
        )
        queue = PlaybackQueue(entries)

        removed_entries = queue.clear()

        self.assertEqual(removed_entries, entries)
        self.assertTrue(queue.is_empty)

    def test_copy_has_independent_storage(self) -> None:
        """Verify that copied queues can be modified independently."""

        entry = QueueEntry(track=self.first_track)
        queue = PlaybackQueue((entry,))
        copied_queue = queue.copy()

        copied_queue.clear()

        self.assertEqual(queue.entries, (entry,))
        self.assertTrue(copied_queue.is_empty)

    def test_contains_accepts_entry_and_identifier(self) -> None:
        """Verify membership checks for entries and UUID identifiers."""

        entry = QueueEntry(track=self.first_track)
        queue = PlaybackQueue((entry,))

        self.assertIn(entry, queue)
        self.assertIn(entry.identifier, queue)
        self.assertNotIn("first", queue)

    def test_slice_returns_immutable_tuple(self) -> None:
        """Verify that queue slices return immutable tuples."""

        entries = (
            QueueEntry(track=self.first_track),
            QueueEntry(track=self.second_track),
        )
        queue = PlaybackQueue(entries)

        self.assertEqual(queue[:1], (entries[0],))

if __name__ == "__main__":
    unittest.main()
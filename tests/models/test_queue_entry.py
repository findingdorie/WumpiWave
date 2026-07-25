"""Tests for the WumpiWave queue entry model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from math import inf, nan
from uuid import UUID, uuid4

from wumpiwave.models import MediaSource, MediaTrack, QueueEntry

class QueueEntryTestCase(unittest.TestCase):
    """Test queue entry creation, validation, and calculated properties."""

    def setUp(self) -> None:
        """Create reusable media tracks for each test."""

        self.track = MediaTrack(
            identifier="track-id",
            source=MediaSource.YOUTUBE,
            title="Example track",
            url="https://www.youtube.com/watch?v=track-id",
            duration=180.0
        )
        self.unknown_duration_track = MediaTrack(
            identifier="live-track",
            source=MediaSource.YOUTUBE,
            title="Live track",
            url="https://www.youtube.com/watch?v=live-track"
        )

    def test_creates_entry_with_expected_defaults(self) -> None:
        """Verify that a queue entry uses safe default values."""

        entry = QueueEntry(track=self.track)

        self.assertIs(entry.track, self.track)
        self.assertIsInstance(entry.identifier, UUID)
        self.assertIsNone(entry.requester_id)
        self.assertIsNotNone(entry.requested_at.tzinfo)
        self.assertEqual(entry.start_position, 0.0)

    def test_generates_unique_identifiers(self) -> None:
        """Verify that separate entries receive unique identifiers."""

        first_entry = QueueEntry(track=self.track)
        second_entry = QueueEntry(track=self.track)

        self.assertNotEqual(
            first_entry.identifier,
            second_entry.identifier
        )

    def test_preserves_complete_entry_metadata(self) -> None:
        """Verify that complete queue entry metadata is retained."""

        identifier = uuid4()
        requested_at = datetime(2026, 7, 25, 8, 0, tzinfo=UTC)
        entry = QueueEntry(
            track=self.track,
            identifier=identifier,
            requester_id=123456789,
            requested_at=requested_at,
            start_position=30.0
        )

        self.assertEqual(entry.identifier, identifier)
        self.assertEqual(entry.requester_id, 123456789)
        self.assertEqual(entry.requested_at, requested_at)
        self.assertEqual(entry.start_position, 30.0)

    def test_has_requester_returns_false_without_requester(self) -> None:
        """Verify that an entry without a requester reports false."""

        entry = QueueEntry(track=self.track)

        self.assertFalse(entry.has_requester)

    def test_has_requester_returns_true_with_requester(self) -> None:
        """Verify that an entry with a requester reports true."""

        entry = QueueEntry(
            track=self.track,
            requester_id=123456789
        )

        self.assertTrue(entry.has_requester)

    def test_remaining_duration_subtracts_start_position(self) -> None:
        """Verify that remaining duration accounts for the start position."""

        entry = QueueEntry(
            track=self.track,
            start_position=30.0
        )

        self.assertEqual(entry.remaining_duration, 150.0)

    def test_remaining_duration_is_none_when_duration_is_unknown(self) -> None:
        """Verify that an unknown track duration produces no remaining value."""

        entry = QueueEntry(
            track=self.unknown_duration_track,
            start_position=30.0
        )

        self.assertIsNone(entry.remaining_duration)

    def test_accepts_start_position_equal_to_duration(self) -> None:
        """Verify that playback may begin at the end of a track."""

        entry = QueueEntry(
            track=self.track,
            start_position=180.0
        )

        self.assertEqual(entry.remaining_duration, 0.0)

    def test_rejects_zero_requester_identifier(self) -> None:
        """Verify that a requester identifier of zero is rejected."""

        with self.assertRaises(ValueError):
            QueueEntry(
                track=self.track,
                requester_id=0
            )

    def test_rejects_negative_requester_identifier(self) -> None:
        """Verify that a negative requester identifier is rejected."""

        with self.assertRaises(ValueError):
            QueueEntry(
                track=self.track,
                requester_id=-1
            )

    def test_rejects_naive_request_datetime(self) -> None:
        """Verify that the request datetime requires timezone data."""

        with self.assertRaises(ValueError):
            QueueEntry(
                track=self.track,
                requested_at=datetime.now()
            )

    def test_rejects_negative_start_position(self) -> None:
        """Verify that a negative start position is rejected."""

        with self.assertRaises(ValueError):
            QueueEntry(
                track=self.track,
                start_position=-1.0
            )

    def test_rejects_infinite_start_position(self) -> None:
        """Verify that an infinite start position is rejected."""

        with self.assertRaises(ValueError):
            QueueEntry(
                track=self.track,
                start_position=inf
            )

    def test_rejects_nan_start_position(self) -> None:
        """Verify that a NaN start position is rejected."""

        with self.assertRaises(ValueError):
            QueueEntry(
                track=self.track,
                start_position=nan
            )

    def test_rejects_start_position_beyond_duration(self) -> None:
        """Verify that playback cannot begin beyond the track duration."""

        with self.assertRaises(ValueError):
            QueueEntry(
                track=self.track,
                start_position=181.0
            )

    def test_entry_is_immutable(self) -> None:
        """Verify that queue entry fields cannot be changed."""

        entry = QueueEntry(track=self.track)

        with self.assertRaises(FrozenInstanceError):
            setattr(entry, "start_position", 30.0)

if __name__ == "__main__":
    unittest.main()
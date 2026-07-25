"""Tests for the WumpiWave playback enumeration models."""

from __future__ import annotations

import unittest
from enum import Enum

from wumpiwave.models import LoopMode, PlayerState, TrackEndReason

class PlaybackEnumTestCase(unittest.TestCase):
    """Test playback-related enumeration definitions and values."""

    def test_loop_mode_is_enum(self) -> None:
        """Verify that loop modes use an enumeration."""

        self.assertTrue(issubclass(LoopMode, Enum))

    def test_loop_mode_contains_members(self) -> None:
        """Verify that at least one loop mode is available."""

        self.assertGreater(len(LoopMode), 0)

    def test_loop_mode_values_are_unique(self) -> None:
        """Verify that loop mode values do not contain duplicates."""

        values = [member.value for member in LoopMode]

        self.assertEqual(len(values), len(set(values)))

    def test_player_state_is_enum(self) -> None:
        """Verify that player states use an enumeration."""

        self.assertTrue(issubclass(PlayerState, Enum))

    def test_player_state_contains_members(self) -> None:
        """Verify that at least one player state is available."""

        self.assertGreater(len(PlayerState), 0)

    def test_player_state_values_are_unique(self) -> None:
        """Verify that player state values do not contain duplicates."""

        values = [member.value for member in PlayerState]

        self.assertEqual(len(values), len(set(values)))

    def test_track_end_reason_is_enum(self) -> None:
        """Verify that track end reasons use an enumeration."""

        self.assertTrue(issubclass(TrackEndReason, Enum))

    def test_track_end_reason_contains_members(self) -> None:
        """Verify that at least one track end reason is available."""

        self.assertGreater(len(TrackEndReason), 0)

    def test_track_end_reason_values_are_unique(self) -> None:
        """Verify that track end reason values do not contain duplicates."""

        values = [member.value for member in TrackEndReason]

        self.assertEqual(len(values), len(set(values)))

if __name__ == "__main__":
    unittest.main()
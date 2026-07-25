"""Tests for the WumpiWave media statistics model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from wumpiwave.models import MediaStatistics

class MediaStatisticsTestCase(unittest.TestCase):
    """Test media statistics creation, validation, and immutability."""

    def test_uses_expected_default_values(self) -> None:
        """Verify that unavailable statistics default to None."""

        statistics = MediaStatistics()

        self.assertIsNone(statistics.view_count)
        self.assertIsNone(statistics.like_count)
        self.assertIsNone(statistics.comment_count)
        self.assertIsNone(statistics.popularity_score)

    def test_preserves_complete_statistics(self) -> None:
        """Verify that complete media statistics are retained."""

        statistics = MediaStatistics(
            view_count=1_000_000,
            like_count=50_000,
            comment_count=2_500,
            popularity_score=85
        )

        self.assertEqual(statistics.view_count, 1_000_000)
        self.assertEqual(statistics.like_count, 50_000)
        self.assertEqual(statistics.comment_count, 2_500)
        self.assertEqual(statistics.popularity_score, 85)

    def test_accepts_partial_statistics(self) -> None:
        """Verify that individual statistics may be omitted."""

        statistics = MediaStatistics(
            view_count=1_000,
            like_count=100
        )

        self.assertEqual(statistics.view_count, 1_000)
        self.assertEqual(statistics.like_count, 100)
        self.assertIsNone(statistics.comment_count)
        self.assertIsNone(statistics.popularity_score)

    def test_accepts_zero_counts(self) -> None:
        """Verify that zero-valued counters are valid."""

        statistics = MediaStatistics(
            view_count=0,
            like_count=0,
            comment_count=0
        )

        self.assertEqual(statistics.view_count, 0)
        self.assertEqual(statistics.like_count, 0)
        self.assertEqual(statistics.comment_count, 0)

    def test_accepts_popularity_boundaries(self) -> None:
        """Verify that popularity scores from zero to one hundred are valid."""

        minimum = MediaStatistics(popularity_score=0)
        maximum = MediaStatistics(popularity_score=100)

        self.assertEqual(minimum.popularity_score, 0)
        self.assertEqual(maximum.popularity_score, 100)

    def test_rejects_negative_view_count(self) -> None:
        """Verify that a negative view count is rejected."""

        with self.assertRaises(ValueError):
            MediaStatistics(view_count=-1)

    def test_rejects_negative_like_count(self) -> None:
        """Verify that a negative like count is rejected."""

        with self.assertRaises(ValueError):
            MediaStatistics(like_count=-1)

    def test_rejects_negative_comment_count(self) -> None:
        """Verify that a negative comment count is rejected."""

        with self.assertRaises(ValueError):
            MediaStatistics(comment_count=-1)

    def test_rejects_negative_popularity_score(self) -> None:
        """Verify that a popularity score below zero is rejected."""

        with self.assertRaises(ValueError):
            MediaStatistics(popularity_score=-1)

    def test_rejects_popularity_score_above_one_hundred(self) -> None:
        """Verify that a popularity score above one hundred is rejected."""

        with self.assertRaises(ValueError):
            MediaStatistics(popularity_score=101)

    def test_statistics_are_immutable(self) -> None:
        """Verify that statistics cannot be changed after creation."""

        statistics = MediaStatistics(view_count=1_000)

        with self.assertRaises(FrozenInstanceError):
            setattr(statistics, "view_count", 2_000)

if __name__ == "__main__":
    unittest.main()
"""Tests for the WumpiWave media track model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from math import inf, nan

from wumpiwave.models import (
    MediaArtist,
    MediaImage,
    MediaSource,
    MediaStatistics,
    MediaTrack,
)


class MediaTrackTestCase(unittest.TestCase):
    """Test media track creation, defaults, validation, and immutability."""

    def test_creates_track_with_required_values(self) -> None:
        """Verify that a track can be created from required metadata."""

        track = MediaTrack(
            identifier="video-id",
            source=MediaSource.YOUTUBE,
            title="Example track",
            url="https://www.youtube.com/watch?v=video-id"
        )

        self.assertEqual(track.identifier, "video-id")
        self.assertIs(track.source, MediaSource.YOUTUBE)
        self.assertEqual(track.title, "Example track")
        self.assertEqual(
            track.url,
            "https://www.youtube.com/watch?v=video-id"
        )

    def test_uses_expected_default_values(self) -> None:
        """Verify that optional track metadata uses safe defaults."""

        track = MediaTrack(
            identifier="track-id",
            source=MediaSource.SPOTIFY,
            title="Example track",
            url="https://www.spotify.com/track/track-id"
        )

        self.assertIsNone(track.duration)
        self.assertEqual(track.artists, ())
        self.assertEqual(track.thumbnails, ())
        self.assertEqual(track.statistics, MediaStatistics())
        self.assertIsNone(track.description)
        self.assertIsNone(track.album_name)
        self.assertIsNone(track.release_date)
        self.assertFalse(track.is_live)
        self.assertFalse(track.is_explicit)

    def test_preserves_complete_metadata(self) -> None:
        """Verify that complete track metadata is retained."""

        artist = MediaArtist(
            name="Example artist",
            identifier="artist-id",
            url="https://example.com/artist"
        )
        thumbnail = MediaImage(
            url="https://example.com/thumbnail.jpg",
            width=1280,
            height=720
        )
        statistics = MediaStatistics(
            view_count=1_00,
            like_count=100,
            comment_count=10,
            popularity_score=75
        )
        track = MediaTrack(
            identifier="track-id",
            source=MediaSource.YOUTUBE,
            title="Example track",
            url="https://example.com/track",
            duration=180.5,
            artists=(artist,),
            thumbnails=(thumbnail,),
            statistics=statistics,
            description="Example description",
            album_name="Example album",
            release_date="2026-07-25",
            is_live=False,
            is_explicit=True
        )

        self.assertEqual(track.duration, 180.5)
        self.assertEqual(track.artists, (artist,))
        self.assertEqual(track.thumbnails, (thumbnail,))
        self.assertIs(track.statistics, statistics)
        self.assertEqual(track.description, "Example description")
        self.assertEqual(track.album_name, "Example album")
        self.assertEqual(track.release_date, "2026-07-25")
        self.assertFalse(track.is_live)
        self.assertTrue(track.is_explicit)

    def test_accepts_zero_duration(self) -> None:
        """Verify that a zero-second duration is valid."""

        track = MediaTrack(
            identifier="track-id",
            source=MediaSource.HTTP,
            title="Empty stream",
            url="https://example.com/audio.mp3",
            duration=0.0
        )

        self.assertEqual(track.duration, 0.0)

    def test_rejects_empty_identifier(self) -> None:
        """Verify that an empty track identifier is rejected."""

        with self.assertRaises(ValueError):
            MediaTrack(
                identifier="",
                source=MediaSource.YOUTUBE,
                title="Example track",
                url="https://example.com/track"
            )

    def test_rejects_whitespace_identifier(self) -> None:
        """Verify that a whitespace-only identifier is rejected."""

        with self.assertRaises(ValueError):
            MediaTrack(
                identifier="   ",
                source=MediaSource.YOUTUBE,
                title="Example track",
                url="https://example.com/track"
            )

    def test_rejects_empty_title(self) -> None:
        """Verify that an empty track title is rejected."""

        with self.assertRaises(ValueError):
            MediaTrack(
                identifier="track-id",
                source=MediaSource.YOUTUBE,
                title="",
                url="https://example.com/track"
            )

    def test_rejects_empty_url(self) -> None:
        """Verify that an empty track URL is rejected."""

        with self.assertRaises(ValueError):
            MediaTrack(
                identifier="track-id",
                source=MediaSource.YOUTUBE,
                title="Example track",
                url=""
            )

    def test_rejects_negative_duration(self) -> None:
        """Verify that a negative duration is rejected."""

        with self.assertRaises(ValueError):
            MediaTrack(
                identifier="track-id",
                source=MediaSource.YOUTUBE,
                title="Example track",
                url="https://example.com/track",
                duration=-1.0
            )

    def test_rejects_infinite_duration(self) -> None:
        """Verify that an infinite duration is rejected."""

        with self.assertRaises(ValueError):
            MediaTrack(
                identifier="track-id",
                source=MediaSource.YOUTUBE,
                title="Example track",
                url="https://example.com/track",
                duration=inf
            )

    def test_rejects_nan_duration(self) -> None:
        """Verify that a NaN duration is rejected."""

        with self.assertRaises(ValueError):
            MediaTrack(
                identifier="track-id",
                source=MediaSource.YOUTUBE,
                title="Example track",
                url="https://example.com/track",
                duration=nan
            )

    def test_track_is_immutable(self) -> None:
        """Verify that track fields cannot be changed after creation."""

        track = MediaTrack(
            identifier="track-id",
            source=MediaSource.YOUTUBE,
            title="Example track",
            url="https://example.com/track"
        )

        with self.assertRaises(FrozenInstanceError):
            setattr(track, "title", "Changed title")

if __name__ == "__main__":
    unittest.main()
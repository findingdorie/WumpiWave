"""Tests for the WumpiWave playable source model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

from wumpiwave.models import MediaSource, PlayableSource

class PlayableSourceTestCase(unittest.TestCase):
    """Test playable source creation, validation, and expiration."""

    def test_creates_source_with_required_values(self) -> None:
        """Verify that a playable source can be created."""

        source = PlayableSource(
            stream_url="https://example.com/audio.mp3",
            source=MediaSource.HTTP
        )

        self.assertEqual(
            source.stream_url,
            "https://example.com/audio.mp3"
        )
        self.assertIs(source.source, MediaSource.HTTP)
        self.assertEqual(dict(source.headers), {})
        self.assertIsNone(source.expires_at)
        self.assertFalse(source.seekable)

    def test_preserves_complete_source_metadata(self) -> None:
        """Verify that complete playable source metadata is retained."""

        expires_at = datetime.now(UTC) + timedelta(minutes=10)
        source = PlayableSource(
            stream_url="https://example.com/audio.mp3",
            source=MediaSource.YOUTUBE,
            headers={
                "Authorization": "Bearer example",
                "User-Agent": "WumpiWave"
            },
            expires_at=expires_at,
            seekable=True
        )

        self.assertEqual(
            dict(source.headers),
            {
                "Authorization": "Bearer example",
                "User-Agent": "WumpiWave"
            }
        )
        self.assertEqual(source.expires_at, expires_at)
        self.assertTrue(source.seekable)

    def test_normalizes_stream_url(self) -> None:
        """Verify that surrounding URL whitespace is removed."""

        source = PlayableSource(
            stream_url="  https://example.com/audio.mp3  ",
            source=MediaSource.HTTP
        )

        self.assertEqual(
            source.stream_url,
            "https://example.com/audio.mp3"
        )

    def test_normalizes_header_names_and_values(self) -> None:
        """Verify that surrounding header whitespace is removed."""

        source = PlayableSource(
            stream_url="https://example.com/audio.mp3",
            source=MediaSource.HTTP,
            headers={
                "  Authorization  ": "  Bearer example  ",
                "  User-Agent": "WumpiWave  "
            }
        )

        self.assertEqual(
            dict(source.headers),
            {
                "Authorization": "Bearer example",
                "User-Agent": "WumpiWave"
            }
        )

    def test_rejects_empty_stream_url(self) -> None:
        """Verify that an empty stream URL is rejected."""

        with self.assertRaises(ValueError):
            PlayableSource(
                stream_url="",
                source=MediaSource.HTTP
            )

    def test_rejects_whitespace_stream_url(self) -> None:
        """Verify that a whitespace-only stream URL is rejected."""

        with self.assertRaises(ValueError):
            PlayableSource(
                stream_url="   ",
                source=MediaSource.HTTP
            )

    def test_rejects_empty_header_name(self) -> None:
        """Verify that an empty HTTP header name is rejected."""

        with self.assertRaises(ValueError):
            PlayableSource(
                stream_url="https://example.com/audio.mp3",
                source=MediaSource.HTTP,
                headers={"": "example"}
            )

    def test_rejects_whitespace_header_name(self) -> None:
        """Verify that a whitespace-only header name is rejected."""

        with self.assertRaises(ValueError):
            PlayableSource(
                stream_url="https://example.com/audio.mp3",
                source=MediaSource.HTTP,
                headers={"   ": "example"}
            )

    def test_rejects_naive_expiration_datetime(self) -> None:
        """Verify that an expiration datetime requires timezone data."""

        with self.assertRaises(ValueError):
            PlayableSource(
                stream_url="https://example.com/audio.mp3",
                source=MediaSource.HTTP,
                expires_at=datetime.now()
            )

    def test_source_without_expiration_never_expires(self) -> None:
        """Verify that a source without expiration remains valid."""

        source = PlayableSource(
            stream_url="https://example.com/audio.mp3",
            source=MediaSource.HTTP
        )

        self.assertFalse(source.expired)
        self.assertIsNone(source.remaining_lifetime)

    def test_future_source_reports_remaining_lifetime(self) -> None:
        """Verify that a future expiration reports remaining seconds."""

        source = PlayableSource(
            stream_url="https://example.com/audio.mp3",
            source=MediaSource.HTTP,
            expires_at=datetime.now(UTC) + timedelta(seconds=60)
        )

        remaining_lifetime = source.remaining_lifetime

        self.assertFalse(source.expired)
        self.assertIsNotNone(remaining_lifetime)
        self.assertGreater(remaining_lifetime, 0.0)
        self.assertLessEqual(remaining_lifetime, 60.0)

    def test_expired_source_reports_zero_lifetime(self) -> None:
        """Verify that an expired source has no remaining lifetime."""

        source = PlayableSource(
            stream_url="https://example.com/audio.mp3",
            source=MediaSource.HTTP,
            expires_at=datetime.now(UTC) - timedelta(seconds=1)
        )

        self.assertTrue(source.expired)
        self.assertEqual(source.remaining_lifetime, 0.0)

    def test_source_is_immutable(self) -> None:
        """Verify that playable source fields cannot be changed."""

        source = PlayableSource(
            stream_url="https://example.com/audio.mp3",
            source=MediaSource.HTTP
        )

        with self.assertRaises(FrozenInstanceError):
            setattr(source, "seekable", True)

if __name__ == "__main__":
    unittest.main()
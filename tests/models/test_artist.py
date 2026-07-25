"""Tests for the WumpiWave media artist model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from wumpiwave.models import MediaArtist

class MediaArtistTestCase(unittest.TestCase):
    """Test media artist creation, validation, and immutability."""


    def test_creates_artist_with_required_name(self) -> None:
        """Verify that an artist can be created with only a name."""

        artist = MediaArtist(name="Example artist")

        self.assertEqual(artist.name, "Example artist")
        self.assertIsNone(artist.identifier)
        self.assertIsNone(artist.url)

    def test_preserves_complete_artist_metadata(self) -> None:
        """Verify that complete artist metadata is retained."""

        artist = MediaArtist(
            name="Example artist",
            identifier="artist-id",
            url="https://example.com/artists/artist-id"
        )

        self.assertEqual(artist.name, "Example artist")
        self.assertEqual(artist.identifier, "artist-id")
        self.assertEqual(
            artist.url,
            "https://example.com/artists/artist-id"
        )

    def test_accepts_missing_identifier(self) -> None:
        """Verify that an artist identifier is optional."""

        artist = MediaArtist(
            name="Example artist",
            url="https://example.com/artist"
        )

        self.assertIsNone(artist.identifier)
        self.assertEqual(artist.url, "https://example.com/artist")

    def test_accepts_missing_url(self) -> None:
        """Verify that an artist URL is optional."""

        artist = MediaArtist(
            name="Example artist",
            identifier="artist-id"
        )

        self.assertEqual(artist.identifier, "artist-id")
        self.assertIsNone(artist.url)

    def test_rejects_empty_name(self) -> None:
        """Verify that an empty artist name is rejected."""

        with self.assertRaises(ValueError):
            MediaArtist(name="")

    def test_rejects_whitespace_name(self) -> None:
        """Verify that a whitespace-only artist name is rejected."""

        with self.assertRaises(ValueError):
            MediaArtist(name="   ")

    def test_artist_is_immutable(self) -> None:
        """Verify that artist fields cannot be changed after creation."""

        artist = MediaArtist(name="Example artist")

        with self.assertRaises(FrozenInstanceError):
            setattr(artist, "name", "Changed artist")

if __name__ == "__main__":
    unittest.main()
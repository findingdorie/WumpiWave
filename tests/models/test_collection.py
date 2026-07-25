"""Tests for the WumpiWave media collection model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from wumpiwave.models import (
    MediaArtist,
    MediaCollection,
    MediaImage,
    MediaSource,
    MediaTrack,
    MediaType,
)

class MediaCollectionTestCase(unittest.TestCase):
    """Test media collection creation, validation, and immutability."""

    def setUp(self) -> None:
        """Create reusable media models for each test."""

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

    def test_creates_playlist_collection(self) -> None:
        """Verify that a playlist collection can be created."""

        collection = MediaCollection(
            identifier="playlist-id",
            source=MediaSource.YOUTUBE,
            media_type=MediaType.PLAYLIST,
            title="Example playlist",
            url="https://www.youtube.com/playlist?list=playlist-id",
            tracks=(
                self.first_track,
                self.second_track
            )
        )

        self.assertEqual(collection.identifier, "playlist-id")
        self.assertIs(collection.source, MediaSource.YOUTUBE)
        self.assertIs(collection.media_type, MediaType.PLAYLIST)
        self.assertEqual(collection.title, "Example playlist")
        self.assertEqual(
            collection.tracks,
            (
                self.first_track,
                self.second_track
            )
        )

    def test_creates_album_collection(self) -> None:
        """Verify that an album collection can be created."""

        collection = MediaCollection(
            identifier="album-id",
            source=MediaSource.SPOTIFY,
            media_type=MediaType.ALBUM,
            title="Example album",
            url="https://open.spotify.com/album/album-id"
        )

        self.assertIs(collection.media_type, MediaType.ALBUM)
        self.assertIs(collection.source, MediaSource.SPOTIFY)

    def test_uses_expected_default_values(self) -> None:
        """Verify that optional collection metadata uses safe defaults."""

        collection = MediaCollection(
            identifier="playlist-id",
            source=MediaSource.YOUTUBE,
            media_type=MediaType.PLAYLIST,
            title="Example playlist",
            url="https://example.com/playlist"
        )

        self.assertEqual(collection.tracks, ())
        self.assertEqual(collection.thumbnails, ())
        self.assertIsNone(collection.author)
        self.assertIsNone(collection.description)

    def test_preserves_complete_metadata(self) -> None:
        """Verify that complete collection metadata is retained."""

        author = MediaArtist(
            name="Example author",
            identifier="author-id",
            url="https://example.com/author"
        )
        thumbnail = MediaImage(
            url="https://example.com/thumbnail.jpg",
            width=640,
            height=640
        )
        collection = MediaCollection(
            identifier="album-id",
            source=MediaSource.SPOTIFY,
            media_type=MediaType.ALBUM,
            title="Example album",
            url="https://open.spotify.com/album/album-id",
            tracks=(self.first_track,),
            thumbnails=(thumbnail,),
            author=author,
            description="Example description"
        )

        self.assertEqual(collection.tracks, (self.first_track,))
        self.assertEqual(collection.thumbnails, (thumbnail,))
        self.assertIs(collection.author, author)
        self.assertEqual(collection.description, "Example description")

    def test_rejects_track_media_type(self) -> None:
        """Verify that a collection cannot use the track media type."""

        with self.assertRaises(ValueError):
            MediaCollection(
                identifier="track-id",
                source=MediaSource.YOUTUBE,
                media_type=MediaType.TRACK,
                title="Invalid collection",
                url="https://example.com/track"
            )

    def test_rejects_empty_identifier(self) -> None:
        """Verify that an empty collection identifier is rejected."""

        with self.assertRaises(ValueError):
            MediaCollection(
                identifier="",
                source=MediaSource.YOUTUBE,
                media_type=MediaType.PLAYLIST,
                title="Example playlist",
                url="https://example.com/playlist"
            )

    def test_rejects_whitespace_identifier(self) -> None:
        """Verify that a whitespace-only identifier is rejected."""

        with self.assertRaises(ValueError):
            MediaCollection(
                identifier="   ",
                source=MediaSource.YOUTUBE,
                media_type=MediaType.PLAYLIST,
                title="Example playlist",
                url="https://example.com/playlist"
            )

    def test_rejects_empty_title(self) -> None:
        """Verify that an empty collection title is rejected."""

        with self.assertRaises(ValueError):
            MediaCollection(
                identifier="playlist-id",
                source=MediaSource.YOUTUBE,
                media_type=MediaType.PLAYLIST,
                title="",
                url="https://example.com/playlist"
            )

    def test_rejects_empty_url(self) -> None:
        """Verify that an empty collection URL is rejected."""

        with self.assertRaises(ValueError):
            MediaCollection(
                identifier="playlist-id",
                source=MediaSource.YOUTUBE,
                media_type=MediaType.PLAYLIST,
                title="Example playlist",
                url=""
            )

    def test_collection_is_immutable(self) -> None:
        """Verify that collection fields cannot be changed after creation."""

        collection = MediaCollection(
            identifier="playlist-id",
            source=MediaSource.YOUTUBE,
            media_type=MediaType.PLAYLIST,
            title="Example playlist",
            url="https://example.com/playlist"
        )

        with self.assertRaises(FrozenInstanceError):
            setattr(collection, "title", "Changed title")

if __name__ == "__main__":
    unittest.main()
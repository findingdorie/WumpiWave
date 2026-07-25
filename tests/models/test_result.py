"""Tests for the WumpiWave media result model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from wumpiwave.models import (
    MediaCollection,
    MediaQuery,
    MediaResult,
    MediaSource,
    MediaTrack,
    MediaType,
    QueryType,
)

class MediaResultTestCase(unittest.TestCase):
    """Test media result tracks, collections, properties, and immutability."""

    def setUp(self) -> None:
        """Create reusable media models for each test."""

        self.query = MediaQuery(
            value="Example track",
            query_type=QueryType.SEARCH,
            source=MediaSource.YOUTUBE,
            limit=10,
            include_statistics=True,
            include_collections=False
        )
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

    def test_creates_result_with_tracks(self) -> None:
        """Verify that a result can contain multiple tracks."""

        result = MediaResult(
            query=self.query,
            source=MediaSource.YOUTUBE,
            tracks=(
                self.first_track,
                self.second_track
            ),
        )

        self.assertIs(result.query, self.query)
        self.assertIs(result.source, MediaSource.YOUTUBE)
        self.assertEqual(
            result.tracks,
            (
                self.first_track,
                self.second_track
            )
        )
        self.assertIsNone(result.collection)

    def test_first_returns_first_track(self) -> None:
        """Verify that the first property returns the first result track."""

        result = MediaResult(
            query=self.query,
            source=MediaSource.YOUTUBE,
            tracks=(
                self.first_track,
                self.second_track
            )
        )

        self.assertIs(result.first, self.first_track)

    def test_first_returns_none_for_empty_result(self) -> None:
        """Verify that an empty result has no first track."""

        result = MediaResult(
            query=self.query,
            source=MediaSource.YOUTUBE
        )

        self.assertIsNone(result.first)

    def test_empty_result_reports_expected_state(self) -> None:
        """Verify that an empty result reports its state correctly."""

        result = MediaResult(
            query=self.query,
            source=MediaSource.YOUTUBE
        )

        self.assertTrue(result.is_empty)
        self.assertFalse(result.is_collection)
        self.assertEqual(result.total_tracks, 0)
        self.assertEqual(len(result), 0)
        self.assertFalse(result)

    def test_track_result_reports_expected_state(self) -> None:
        """Verify that a track result reports its size correctly."""

        result = MediaResult(
            query=self.query,
            source=MediaSource.YOUTUBE,
            tracks=(
                self.first_track,
                self.second_track
            )
        )

        self.assertFalse(result.is_empty)
        self.assertFalse(result.is_collection)
        self.assertEqual(result.total_tracks, 2)
        self.assertEqual(len(result), 2)
        self.assertTrue(result)

    def test_collection_result_uses_collection_tracks(self) -> None:
        """Verify that omitted result tracks are derived from a collection."""

        collection = MediaCollection(
            identifier="playlist-id",
            source=MediaSource.YOUTUBE,
            media_type=MediaType.PLAYLIST,
            title="Example playlist",
            url="https://www.youtube.com/playlist?list=playlist-id",
            tracks=(
                self.first_track,
                self.second_track
            ),
        )
        result = MediaResult(
            query=self.query,
            source=MediaSource.YOUTUBE,
            collection=collection
        )

        self.assertEqual(
            result.tracks,
            (
                self.first_track,
                self.second_track
            )
        )
        self.assertIs(result.collection, collection)
        self.assertTrue(result.is_collection)
        self.assertFalse(result.is_empty)
        self.assertEqual(result.total_tracks, 2)
        self.assertIs(result.first, self.first_track)

    def test_explicit_tracks_are_preserved_with_collection(self) -> None:
        """Verify that explicit result tracks are not replaced."""

        collection = MediaCollection(
            identifier="playlist-id",
            source=MediaSource.YOUTUBE,
            media_type=MediaType.PLAYLIST,
            title="Example playlist",
            url="https://www.youtube.com/playlist?list=playlist-id",
            tracks=(
                self.first_track,
                self.second_track
            ),
        )
        result = MediaResult(
            query=self.query,
            source=MediaSource.YOUTUBE,
            tracks=(self.second_track,),
            collection=collection
        )

        self.assertEqual(result.tracks, (self.second_track,))
        self.assertEqual(result.total_tracks, 1)
        self.assertTrue(result.is_collection)

    def test_result_is_immutable(self) -> None:
        """Verify that result fields cannot be changed after creation."""

        result = MediaResult(
            query=self.query,
            source=MediaSource.YOUTUBE,
            tracks=(self.first_track,)
        )

        with self.assertRaises(FrozenInstanceError):
            setattr(result, "tracks", ())

if __name__ == "__main__":
    unittest.main()
"""Tests for the WumpiWave media enumeration models."""

from __future__ import annotations

import unittest
from enum import Enum

from wumpiwave.models import MediaSource, MediaType, QueryType

class MediaEnumTestCase(unittest.TestCase):
    """Test media source, type, and query enumerations."""

    def test_media_source_is_enum(self) -> None:
        """Verify that media sources are enumeration members."""

        self.assertIsInstance(MediaSource.YOUTUBE, Enum)
        self.assertIsInstance(MediaSource.SPOTIFY, Enum)
        self.assertIsInstance(MediaSource.HTTP, Enum)

    def test_media_sources_are_distinct(self) -> None:
        """Verify that every supported media source is unique."""

        sources = {
            MediaSource.YOUTUBE,
            MediaSource.SPOTIFY,
            MediaSource.HTTP
        }

        self.assertEqual(len(sources), 3)

    def test_media_type_is_enum(self) -> None:
        """Verify that media types are enumeration members."""

        self.assertIsInstance(MediaType.TRACK, Enum)
        self.assertIsInstance(MediaType.PLAYLIST, Enum)
        self.assertIsInstance(MediaType.ALBUM, Enum)

    def test_media_types_are_distinct(self) -> None:
        """Verify that every supported media type is unique."""

        media_types = {
            MediaType.TRACK,
            MediaType.PLAYLIST,
            MediaType.ALBUM
        }

        self.assertEqual(len(media_types), 3)

    def test_query_type_is_enum(self) -> None:
        """Verify that query types are enumeration members."""

        self.assertIsInstance(QueryType.SEARCH, Enum)
        self.assertIsInstance(QueryType.URL, Enum)

    def test_query_types_are_distinct(self) -> None:
        """Verify that every supported query type is unique."""

        query_types = {
            QueryType.SEARCH,
            QueryType.URL
        }

        self.assertEqual(len(query_types), 2)

if __name__ == "__main__":
    unittest.main()
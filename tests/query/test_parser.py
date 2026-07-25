"""Tests for the WumpiWave media query parser."""

from __future__ import annotations

import unittest

from wumpiwave.exceptions.query import InvalidQueryError
from wumpiwave.models import MediaSource, QueryType
from wumpiwave.query.parser import QueryParser

class QueryParserTestCase(unittest.TestCase):
    """Test media query parsing, detection, options, and validation."""

    def setUp(self) -> None:
        """Create a query parser for each test."""

        self.parser = QueryParser()

    def test_parses_search_query(self) -> None:
        """Verify that plain text is parsed as a search query."""

        query = self.parser.parse("Imagine Dragons Believer")

        self.assertEqual(query.value, "Imagine Dragons Believer")
        self.assertIs(query.query_type, QueryType.SEARCH)
        self.assertIsNone(query.source)

    def test_normalizes_query_value(self) -> None:
        """Verify that surrounding query whitespace is removed."""

        query = self.parser.parse("  Example track  ")

        self.assertEqual(query.value, "Example track")

    def test_uses_preferred_source_for_search_query(self) -> None:
        """Verify that search queries preserve a preferred source."""

        query = self.parser.parse(
            "Example track",
            preferred_source=MediaSource.SPOTIFY
        )

        self.assertIs(query.source, MediaSource.SPOTIFY)

    def test_detects_youtube_url(self) -> None:
        """Verify that YouTube URLs use the YouTube source."""

        query = self.parser.parse("https://www.youtube.com/watch?v=example")

        self.assertIs(query.query_type, QueryType.URL)
        self.assertIs(query.source, MediaSource.YOUTUBE)

    def test_detects_spotify_url(self) -> None:
        """Verify that Spotify URLs use the Spotify source."""

        query = self.parser.parse("https://open.spotify.com/track/example")

        self.assertIs(query.query_type, QueryType.URL)
        self.assertIs(query.source, MediaSource.SPOTIFY)

    def test_detects_direct_http_url(self) -> None:
        """Verify that generic URLs use the HTTP source."""

        query = self.parser.parse("https://example.com/audio.mp3")

        self.assertIs(query.query_type, QueryType.URL)
        self.assertIs(query.source, MediaSource.HTTP)

    def test_preserves_query_options(self) -> None:
        """Verify that result and metadata options are preserved."""

        query = self.parser.parse(
            "Example track",
            result_limit=5,
            include_statistics=False,
            include_collections=False
        )

        self.assertEqual(query.limit, 5)
        self.assertFalse(query.include_statistics)
        self.assertFalse(query.include_collections)

    def test_detect_query_type_returns_search(self) -> None:
        """Verify that plain text is detected as a search query."""

        query_type = self.parser.detect_query_type("Example track")

        self.assertIs(query_type, QueryType.SEARCH)

    def test_detect_query_type_returns_url(self) -> None:
        """Verify that a valid URL is detected as a URL query."""

        query_type = self.parser.detect_query_type("https://example.com/audio.mp3")

        self.assertIs(query_type, QueryType.URL)

    def test_accepts_matching_preferred_url_source(self) -> None:
        """Verify that a matching preferred URL source is accepted."""

        query = self.parser.parse(
            "https://www.youtube.com/watch?v=example",
            preferred_source=MediaSource.YOUTUBE
        )

        self.assertIs(query.source, MediaSource.YOUTUBE)

    def test_rejects_conflicting_preferred_url_source(self) -> None:
        """Verify that a conflicting preferred URL source is rejected."""

        with self.assertRaises(InvalidQueryError):
            self.parser.parse(
                "https://www.youtube.com/watch?v=example",
                preferred_source=MediaSource.SPOTIFY
            )

    def test_rejects_empty_query(self) -> None:
        """Verify that an empty query is rejected."""

        with self.assertRaises(InvalidQueryError):
            self.parser.parse("")

    def test_rejects_whitespace_query(self) -> None:
        """Verify that a whitespace-only query is rejected."""

        with self.assertRaises(InvalidQueryError):
            self.parser.parse("   ")

if __name__ == "__main__":
    unittest.main()
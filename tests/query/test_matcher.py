"""Tests for the WumpiWave media query matcher."""

from __future__ import annotations

import unittest

from wumpiwave.models import MediaSource
from wumpiwave.query.matcher import QueryMatcher

class QueryMatcherTestCase(unittest.TestCase):
    """Test URL recognition and media source matching."""

    def test_recognizes_http_url(self) -> None:
        """Verify that an HTTP URL is recognized."""

        self.assertTrue(
            QueryMatcher.is_url("http://example.com/audio.mp3")
        )

    def test_recognizes_https_url(self) -> None:
        """Verify that an HTTPS URL is recognized."""

        self.assertTrue(
            QueryMatcher.is_url("https://example.com/audio.mp3")
        )

    def test_rejects_plain_search_text_as_url(self) -> None:
        """Verify that plain search text is not recognized as a URL."""

        self.assertFalse(QueryMatcher.is_url("Example artist track"))

    def test_rejects_unsupported_url_scheme(self) -> None:
        """Verify that unsupported URL schemes are rejected."""

        self.assertFalse(QueryMatcher.is_url("ftp://example.com/audio.mp3"))

    def test_rejects_url_without_hostname(self) -> None:
        """Verify that a URL without a hostname is rejected."""

        self.assertFalse(QueryMatcher.is_url("https:///audio.mp3"))

    def test_detects_youtube_domain(self) -> None:
        """Verify that standard YouTube URLs are detected."""

        source = QueryMatcher.detect_source("https://www.youtube.com/watch?v=example")

        self.assertIs(source, MediaSource.YOUTUBE)

    def test_detects_youtube_subdomain(self) -> None:
        """Verify that YouTube subdomains are detected."""

        source = QueryMatcher.detect_source("https://music.youtube.com/watch?v=example")

        self.assertIs(source, MediaSource.YOUTUBE)

    def test_detects_youtube_short_domain(self) -> None:
        """Verify that shortened YouTube URLs are detected."""

        source = QueryMatcher.detect_source("https://youtu.be/example")

        self.assertIs(source, MediaSource.YOUTUBE)

    def test_detects_youtube_nocookie_domain(self) -> None:
        """Verify that YouTube privacy-enhanced URLs are detected."""

        source = QueryMatcher.detect_source("https://www.youtube-nocookie.com/embed/example")

        self.assertIs(source, MediaSource.YOUTUBE)

    def test_detects_spotify_domain(self) -> None:
        """Verify that Spotify URLs are detected."""

        source = QueryMatcher.detect_source("https://open.spotify.com/track/example")

        self.assertIs(source, MediaSource.SPOTIFY)

    def test_detects_generic_http_source(self) -> None:
        """Verify that other valid URLs use the HTTP source."""

        source = QueryMatcher.detect_source("https://example.com/audio.mp3")

        self.assertIs(source, MediaSource.HTTP)

    def test_returns_none_for_non_url(self) -> None:
        """Verify that plain search text has no detected source."""

        source = QueryMatcher.detect_source("Example artist track")

        self.assertIsNone(source)

    def test_does_not_match_spoofed_youtube_domain(self) -> None:
        """Verify that a spoofed YouTube hostname is not trusted."""

        source = QueryMatcher.detect_source("https://youtube.com.example.com/audio.mp3")

        self.assertIs(source, MediaSource.HTTP)

    def test_does_not_match_spoofed_spotify_domain(self) -> None:
        """Verify that a spoofed Spotify hostname is not trusted."""

        source = QueryMatcher.detect_source("https://spotify.com.example.com/audio.mp3")

        self.assertIs(source, MediaSource.HTTP)

    def test_matches_correct_source(self) -> None:
        """Verify that a URL matches its detected media source."""

        self.assertTrue(
            QueryMatcher.matches_source(
                "https://open.spotify.com/track/example",
                MediaSource.SPOTIFY
            )
        )

    def test_rejects_incorrect_source(self) -> None:
        """Verify that a URL does not match another media source."""

        self.assertFalse(
            QueryMatcher.matches_source(
                "https://open.spotify.com/track/example",
                MediaSource.YOUTUBE
            )
        )

    def test_non_url_does_not_match_source(self) -> None:
        """Verify that plain search text does not match a source."""

        self.assertFalse(
            QueryMatcher.matches_source(
                "Example artist track",
                MediaSource.HTTP
            )
        )

if __name__ == "__main__":
    unittest.main()
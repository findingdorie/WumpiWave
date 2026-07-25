"""Tests for the WumpiWave media query model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from wumpiwave.models import MediaQuery, MediaSource, QueryType

class MediaQueryTestCase(unittest.TestCase):
    """Test media query creation, normalization, validation, and immutability."""

    def test_creates_search_query(self) -> None:
        """Verify that a text-based search query can be created."""

        query = MediaQuery(
            value="Imagine Dragons Believer",
            query_type=QueryType.SEARCH,
            source=MediaSource.YOUTUBE,
            limit=5,
            include_statistics=True,
            include_collections=False
        )

        self.assertEqual(query.value, "Imagine Dragons Believer")
        self.assertIs(query.query_type, QueryType.SEARCH)
        self.assertIs(query.source, MediaSource.YOUTUBE)
        self.assertEqual(query.limit, 5)
        self.assertTrue(query.include_statistics)
        self.assertFalse(query.include_collections)

    def test_creates_url_query(self) -> None:
        """Verify that a URL query can be created."""

        query = MediaQuery(
            value="https://www.youtube.com/watch?v=example",
            query_type=QueryType.URL,
            source=MediaSource.YOUTUBE,
            limit=1,
            include_statistics=False,
            include_collections=False
        )

        self.assertEqual(query.value, "https://www.youtube.com/watch?v=example")
        self.assertIs(query.query_type, QueryType.URL)

    def test_accepts_unspecified_source(self) -> None:
        """Verify that a query does not require a preferred source."""

        query = MediaQuery(
            value="Example track",
            query_type=QueryType.SEARCH,
            source=None,
            limit=10,
            include_statistics=True,
            include_collections=False
        )

        self.assertIsNone(query.source)

    def test_normalizes_query_value(self) -> None:
        """Verify that surrounding whitespace is removed."""

        query = MediaQuery(
            value="  Example track  ",
            query_type=QueryType.SEARCH,
            limit=10,
            include_statistics=True,
            include_collections=False
        )

        self.assertEqual(query.value, "Example track")

    def test_accepts_minimum_result_limit(self) -> None:
        """Verify that a result limit of one is valid."""

        query = MediaQuery(
            value="Example track",
            query_type=QueryType.SEARCH,
            limit=1,
            include_statistics=True,
            include_collections=False
        )

        self.assertEqual(query.limit, 1)

    def test_rejects_empty_value(self) -> None:
        """Verify that an empty query value is rejected."""

        with self.assertRaises(ValueError):
            MediaQuery(
                value="",
                query_type=QueryType.SEARCH,
                limit=10,
                include_statistics=True,
                include_collections=False
            )

    def test_rejects_whitespace_value(self) -> None:
        """Verify that a whitespace-only query value is rejected."""

        with self.assertRaises(ValueError):
            MediaQuery(
                value="   ",
                query_type=QueryType.SEARCH,
                limit=10,
                include_statistics=True,
                include_collections=False
            )

    def test_rejects_zero_result_limit(self) -> None:
        """Verify that a result limit of zero is rejected."""

        with self.assertRaises(ValueError):
            MediaQuery(
                value="Example track",
                query_type=QueryType.SEARCH,
                limit=0,
                include_statistics=True,
                include_collections=False
            )

    def test_rejects_negative_result_limit(self) -> None:
        """Verify that a negative result limit is rejected."""

        with self.assertRaises(ValueError):
            MediaQuery(
                value="Example track",
                query_type=QueryType.SEARCH,
                limit=-1,
                include_statistics=True,
                include_collections=False
            )

    def test_query_is_immutable(self) -> None:
        """Verify that query fields cannot be changed after creation."""

        query = MediaQuery(
            value="Example track",
            query_type=QueryType.SEARCH,
            limit=10,
            include_statistics=True,
            include_collections=False
        )

        with self.assertRaises(FrozenInstanceError):
            setattr(query, "value", "Changed query")

if __name__ == "__main__":
    unittest.main()
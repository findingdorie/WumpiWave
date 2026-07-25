"""Tests for the WumpiWave media image model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from wumpiwave.models import MediaImage

class MediaImageTestCase(unittest.TestCase):
    """Test media image creation, validation, and immutability."""

    def test_creates_image_with_required_url(self) -> None:
        """Verify that an image can be created with only a URL."""

        image = MediaImage(url="https://example.com/image.jpg")

        self.assertEqual(image.url, "https://example.com/image.jpg")
        self.assertIsNone(image.width)
        self.assertIsNone(image.height)

    def test_preserves_complete_image_metadata(self) -> None:
        """Verify that complete image metadata is retained."""

        image = MediaImage(
            url="https://example.com/image.jpg",
            width=1280,
            height=720
        )

        self.assertEqual(image.url, "https://example.com/image.jpg")
        self.assertEqual(image.width, 1280)
        self.assertEqual(image.height, 720)

    def test_accepts_only_width(self) -> None:
        """Verify that an image may contain only its width."""

        image = MediaImage(
            url="https://example.com/image.jpg",
            width=1280
        )

        self.assertEqual(image.width, 1280)
        self.assertIsNone(image.height)

    def test_accepts_only_height(self) -> None:
        """Verify that an image may contain only its height."""

        image = MediaImage(
            url="https://example.com/image.jpg",
            height=720
        )

        self.assertIsNone(image.width)
        self.assertEqual(image.height, 720)

    def test_rejects_empty_url(self) -> None:
        """Verify that an empty image URL is rejected."""

        with self.assertRaises(ValueError):
            MediaImage(url="")

    def test_rejects_whitespace_url(self) -> None:
        """Verify that a whitespace-only image URL is rejected."""

        with self.assertRaises(ValueError):
            MediaImage(url="   ")

    def test_rejects_zero_width(self) -> None:
        """Verify that an image width of zero is rejected."""

        with self.assertRaises(ValueError):
            MediaImage(
                url="https://example.com/image.jpg",
                width=0
            )

    def test_rejects_negative_width(self) -> None:
        """Verify that a negative image width is rejected."""

        with self.assertRaises(ValueError):
            MediaImage(
                url="https://example.com/image.jpg",
                width=-1
            )

    def test_rejects_zero_height(self) -> None:
        """Verify that an image height of zero is rejected."""

        with self.assertRaises(ValueError):
            MediaImage(
                url="https://example.com/image.jpg",
                height=0
            )

    def test_rejects_negative_height(self) -> None:
        """Verify that a negative image height is rejected."""

        with self.assertRaises(ValueError):
            MediaImage(
                url="https://example.com/image.jpg",
                height=-1
            )

    def test_image_is_immutable(self) -> None:
        """Verify that image fields cannot be changed after creation."""

        image = MediaImage(url="https://example.com/image.jpg")

        with self.assertRaises(FrozenInstanceError):
            setattr(image, "url", "https://example.com/changed.jpg")

if __name__ == "__main__":
    unittest.main()
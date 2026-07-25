"""Tests for the WumpiWave equalizer audio filter."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from math import inf, nan

from wumpiwave.filters.equalizer import (
    EqualizerBand,
    EqualizerFilter,
)

class EqualizerBandTestCase(unittest.TestCase):
    """Test equalizer band creation, validation, and rendering."""

    def test_creates_band_with_default_width(self) -> None:
        """Verify that a band uses the expected default width."""

        band = EqualizerBand(
            frequency=1_000.0,
            gain=3.0
        )

        self.assertEqual(band.frequency, 1_000.0)
        self.assertEqual(band.gain, 3.0)
        self.assertEqual(band.width, 1.0)

    def test_preserves_complete_band_configuration(self) -> None:
        """Verify that complete band configuration is retained."""

        band = EqualizerBand(
            frequency=250.0,
            gain=-4.5,
            width=1.25
        )

        self.assertEqual(band.frequency, 250.0)
        self.assertEqual(band.gain, -4.5)
        self.assertEqual(band.width, 1.25)

    def test_renders_ffmpeg_expression(self) -> None:
        """Verify that a band renders a valid FFmpeg expression."""

        band = EqualizerBand(
            frequency=1_000.0,
            gain=3.0,
            width=1.5
        )

        self.assertEqual(
            band.render(),
            "equalizer=f=1000:t=q:w=1.5:g=3"
        )

    def test_accepts_negative_gain(self) -> None:
        """Verify that a negative finite gain is valid."""

        band = EqualizerBand(
            frequency=500.0,
            gain=-6.0
        )

        self.assertEqual(band.gain, -6.0)

    def test_accepts_zero_gain(self) -> None:
        """Verify that a zero gain value is valid."""

        band = EqualizerBand(
            frequency=500.0,
            gain=0.0
        )

        self.assertEqual(band.gain, 0.0)

    def test_rejects_zero_frequency(self) -> None:
        """Verify that a zero frequency is rejected."""

        with self.assertRaises(ValueError):
            EqualizerBand(
                frequency=0.0,
                gain=3.0
            )

    def test_rejects_negative_frequency(self) -> None:
        """Verify that a negative frequency is rejected."""

        with self.assertRaises(ValueError):
            EqualizerBand(
                frequency=-1.0,
                gain=3.0
            )

    def test_rejects_infinite_frequency(self) -> None:
        """Verify that an infinite frequency is rejected."""

        with self.assertRaises(ValueError):
            EqualizerBand(
                frequency=inf,
                gain=3.0
            )

    def test_rejects_nan_frequency(self) -> None:
        """Verify that a NaN frequency is rejected."""

        with self.assertRaises(ValueError):
            EqualizerBand(
                frequency=nan,
                gain=3.0
            )

    def test_rejects_infinite_gain(self) -> None:
        """Verify that an infinite gain is rejected."""

        with self.assertRaises(ValueError):
            EqualizerBand(
                frequency=1_000.0,
                gain=inf
            )

    def test_rejects_nan_gain(self) -> None:
        """Verify that a NaN gain is rejected."""

        with self.assertRaises(ValueError):
            EqualizerBand(
                frequency=1_000.0,
                gain=nan
            )

    def test_rejects_zero_width(self) -> None:
        """Verify that a zero Q-factor width is rejected."""

        with self.assertRaises(ValueError):
            EqualizerBand(
                frequency=1_000.0,
                gain=3.0,
                width=0.0
            )

    def test_rejects_negative_width(self) -> None:
        """Verify that a negative Q-factor width is rejected."""

        with self.assertRaises(ValueError):
            EqualizerBand(
                frequency=1_000.0,
                gain=3.0,
                width=-1.0
            )

    def test_rejects_infinite_width(self) -> None:
        """Verify that an infinite Q-factor width is rejected."""

        with self.assertRaises(ValueError):
            EqualizerBand(
                frequency=1_000.0,
                gain=3.0,
                width=inf
            )

    def test_rejects_nan_width(self) -> None:
        """Verify that a NaN Q-factor width is rejected."""

        with self.assertRaises(ValueError):
            EqualizerBand(
                frequency=1_000.0,
                gain=3.0,
                width=nan
            )

    def test_band_is_immutable(self) -> None:
        """Verify that equalizer band fields cannot be changed."""

        band = EqualizerBand(
            frequency=1_000.0,
            gain=3.0
        )

        with self.assertRaises(FrozenInstanceError):
            setattr(band, "gain", 5.0)

class EqualizerFilterTestCase(unittest.TestCase):
    """Test equalizer filter management, indexing, and rendering."""

    def setUp(self) -> None:
        """Create reusable equalizer bands for each test."""

        self.low_band = EqualizerBand(
            frequency=100.0,
            gain=2.0
        )
        self.mid_band = EqualizerBand(
            frequency=1_000.0,
            gain=-3.0,
            width=1.5
        )
        self.high_band = EqualizerBand(
            frequency=8_000.0,
            gain=4.0,
            width=2.0
        )

    def test_creates_empty_equalizer(self) -> None:
        """Verify that a new equalizer contains no bands."""

        equalizer = EqualizerFilter()

        self.assertEqual(equalizer.name, "equalizer")
        self.assertEqual(equalizer.bands, ())
        self.assertEqual(equalizer.band_count, 0)
        self.assertEqual(len(equalizer), 0)
        self.assertTrue(equalizer.enabled)

    def test_initializes_with_bands_in_order(self) -> None:
        """Verify that initialization preserves band order."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.mid_band
            )
        )

        self.assertEqual(
            equalizer.bands,
            (
                self.low_band,
                self.mid_band
            )
        )
        self.assertEqual(equalizer.band_count, 2)

    def test_add_appends_band(self) -> None:
        """Verify that one band can be appended."""

        equalizer = EqualizerFilter()

        result = equalizer.add(self.low_band)

        self.assertIs(result, equalizer)
        self.assertEqual(equalizer.bands, (self.low_band,))

    def test_add_rejects_invalid_value(self) -> None:
        """Verify that non-band values are rejected."""

        equalizer = EqualizerFilter()

        with self.assertRaises(TypeError):
            equalizer.add(object())  # type: ignore[arg-type]

        self.assertEqual(equalizer.bands, ())

    def test_extend_appends_multiple_bands(self) -> None:
        """Verify that multiple bands can be appended together."""

        equalizer = EqualizerFilter((self.low_band,))

        result = equalizer.extend(
            (
                self.mid_band,
                self.high_band
            )
        )

        self.assertIs(result, equalizer)
        self.assertEqual(
            equalizer.bands,
            (
                self.low_band,
                self.mid_band,
                self.high_band
            )
        )

    def test_extend_is_atomic_for_invalid_values(self) -> None:
        """Verify that invalid extension does not modify the equalizer."""

        equalizer = EqualizerFilter((self.low_band,))

        with self.assertRaises(TypeError):
            equalizer.extend(
                (
                    self.mid_band,
                    object()  # type: ignore[arg-type]
                )
            )

        self.assertEqual(equalizer.bands, (self.low_band,))

    def test_get_returns_band_by_index(self) -> None:
        """Verify that a band can be retrieved by index."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.mid_band
            )
        )

        self.assertIs(equalizer.get(0), self.low_band)
        self.assertIs(equalizer.get(1), self.mid_band)

    def test_get_supports_negative_index(self) -> None:
        """Verify that negative band indexes are supported."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.mid_band
            )
        )

        self.assertIs(equalizer.get(-1), self.mid_band)
        self.assertIs(equalizer.get(-2), self.low_band)

    def test_get_rejects_index_outside_bands(self) -> None:
        """Verify that an invalid band index is rejected."""

        equalizer = EqualizerFilter((self.low_band,))

        with self.assertRaises(IndexError):
            equalizer.get(1)

        with self.assertRaises(IndexError):
            equalizer.get(-2)

    def test_replace_returns_previous_band(self) -> None:
        """Verify that replacing returns the previous band."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.mid_band
            )
        )

        previous_band = equalizer.replace(
            0,
            self.high_band
        )

        self.assertIs(previous_band, self.low_band)
        self.assertEqual(
            equalizer.bands,
            (
                self.high_band,
                self.mid_band
            )
        )

    def test_replace_rejects_invalid_band(self) -> None:
        """Verify that replacing requires an EqualizerBand instance."""

        equalizer = EqualizerFilter((self.low_band,))

        with self.assertRaises(TypeError):
            equalizer.replace(
                0,
                object()  # type: ignore[arg-type]
            )

        self.assertEqual(equalizer.bands, (self.low_band,))

    def test_remove_returns_removed_band(self) -> None:
        """Verify that removing returns the selected band."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.mid_band
            )
        )

        removed_band = equalizer.remove(-1)

        self.assertIs(removed_band, self.mid_band)
        self.assertEqual(equalizer.bands, (self.low_band,))

    def test_clear_returns_all_bands_in_order(self) -> None:
        """Verify that clearing returns and removes every band."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.mid_band
            )
        )

        removed_bands = equalizer.clear()

        self.assertEqual(
            removed_bands,
            (
                self.low_band,
                self.mid_band
            )
        )
        self.assertEqual(equalizer.bands, ())
        self.assertEqual(equalizer.band_count, 0)

    def test_build_expression_combines_bands_in_order(self) -> None:
        """Verify that configured bands render in their current order."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.mid_band
            )
        )

        self.assertEqual(
            equalizer.build_expression(),
            (
                "equalizer=f=100:t=q:w=1:g=2,"
                "equalizer=f=1000:t=q:w=1.5:g=-3"
            )
        )

    def test_render_returns_combined_expression(self) -> None:
        """Verify that the enabled equalizer renders its bands."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.high_band
            )
        )

        self.assertEqual(
            equalizer.render(),
            (
                "equalizer=f=100:t=q:w=1:g=2,"
                "equalizer=f=8000:t=q:w=2:g=4"
            )
        )

    def test_enabled_empty_equalizer_cannot_render(self) -> None:
        """Verify that an enabled equalizer requires at least one band."""

        equalizer = EqualizerFilter()

        with self.assertRaises(ValueError):
            equalizer.render()

    def test_disabled_empty_equalizer_returns_none(self) -> None:
        """Verify that a disabled empty equalizer skips rendering."""

        equalizer = EqualizerFilter(enabled=False)

        self.assertIsNone(equalizer.render())
        self.assertEqual(str(equalizer), "")

    def test_getitem_returns_band(self) -> None:
        """Verify that integer subscription returns one band."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.mid_band
            )
        )

        self.assertIs(equalizer[0], self.low_band)
        self.assertIs(equalizer[-1], self.mid_band)

    def test_getitem_returns_immutable_slice(self) -> None:
        """Verify that slicing returns a tuple of bands."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.mid_band,
                self.high_band
            )
        )

        self.assertEqual(
            equalizer[1:],
            (
                self.mid_band,
                self.high_band
            )
        )
        self.assertIsInstance(equalizer[1:], tuple)

    def test_iteration_preserves_band_order(self) -> None:
        """Verify that iteration follows the configured band order."""

        equalizer = EqualizerFilter(
            (
                self.low_band,
                self.mid_band,
                self.high_band
            )
        )

        self.assertEqual(
            tuple(equalizer),
            (
                self.low_band,
                self.mid_band,
                self.high_band
            )
        )

if __name__ == "__main__":
    unittest.main()
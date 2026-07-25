"""Tests for the WumpiWave timescale audio filter."""

from __future__ import annotations

import unittest
from math import inf, nan

from wumpiwave.filters.timescale import TimescaleFilter

class TimescaleFilterTestCase(unittest.TestCase):
    """Test timescale configuration, validation, and rendering."""

    def test_creates_filter_with_expected_defaults(self) -> None:
        """Verify that default timescale values are configured."""

        audio_filter = TimescaleFilter()

        self.assertEqual(audio_filter.name, "timescale")
        self.assertEqual(audio_filter.speed, 1.0)
        self.assertEqual(audio_filter.pitch, 1.0)
        self.assertEqual(audio_filter.sample_rate, 48_000)
        self.assertTrue(audio_filter.enabled)

    def test_preserves_complete_configuration(self) -> None:
        """Verify that supplied timescale values are retained."""

        audio_filter = TimescaleFilter(
            speed=1.5,
            pitch=1.25,
            sample_rate=44_100,
            enabled=False
        )

        self.assertEqual(audio_filter.speed, 1.5)
        self.assertEqual(audio_filter.pitch, 1.25)
        self.assertEqual(audio_filter.sample_rate, 44_100)
        self.assertFalse(audio_filter.enabled)

    def test_accepts_speed_boundaries(self) -> None:
        """Verify that minimum and maximum speeds are accepted."""

        minimum = TimescaleFilter(speed=0.25)
        maximum = TimescaleFilter(speed=4.0)

        self.assertEqual(minimum.speed, 0.25)
        self.assertEqual(maximum.speed, 4.0)

    def test_rejects_speed_below_minimum(self) -> None:
        """Verify that speeds below the supported range are rejected."""

        with self.assertRaises(ValueError):
            TimescaleFilter(speed=0.24)

    def test_rejects_speed_above_maximum(self) -> None:
        """Verify that speeds above the supported range are rejected."""

        with self.assertRaises(ValueError):
            TimescaleFilter(speed=4.01)

    def test_rejects_infinite_speed(self) -> None:
        """Verify that an infinite speed is rejected."""

        with self.assertRaises(ValueError):
            TimescaleFilter(speed=inf)

    def test_rejects_nan_speed(self) -> None:
        """Verify that a NaN speed is rejected."""

        with self.assertRaises(ValueError):
            TimescaleFilter(speed=nan)

    def test_rejects_boolean_speed(self) -> None:
        """Verify that booleans are not accepted as speed values."""

        with self.assertRaises(ValueError):
            TimescaleFilter(speed=True)

    def test_accepts_pitch_boundaries(self) -> None:
        """Verify that minimum and maximum pitches are accepted."""

        minimum = TimescaleFilter(pitch=0.5)
        maximum = TimescaleFilter(pitch=2.0)

        self.assertEqual(minimum.pitch, 0.5)
        self.assertEqual(maximum.pitch, 2.0)

    def test_rejects_pitch_below_minimum(self) -> None:
        """Verify that pitches below the supported range are rejected."""

        with self.assertRaises(ValueError):
            TimescaleFilter(pitch=0.49)

    def test_rejects_pitch_above_maximum(self) -> None:
        """Verify that pitches above the supported range are rejected."""

        with self.assertRaises(ValueError):
            TimescaleFilter(pitch=2.01)

    def test_rejects_infinite_pitch(self) -> None:
        """Verify that an infinite pitch is rejected."""

        with self.assertRaises(ValueError):
            TimescaleFilter(pitch=inf)

    def test_rejects_nan_pitch(self) -> None:
        """Verify that a NaN pitch is rejected."""

        with self.assertRaises(ValueError):
            TimescaleFilter(pitch=nan)

    def test_rejects_boolean_pitch(self) -> None:
        """Verify that booleans are not accepted as pitch values."""

        with self.assertRaises(ValueError):
            TimescaleFilter(pitch=False)

    def test_accepts_positive_sample_rate(self) -> None:
        """Verify that a positive integer sample rate is accepted."""

        audio_filter = TimescaleFilter(sample_rate=96_000)

        self.assertEqual(audio_filter.sample_rate, 96_000)

    def test_rejects_zero_sample_rate(self) -> None:
        """Verify that a zero sample rate is rejected."""

        with self.assertRaises(ValueError):
            TimescaleFilter(sample_rate=0)

    def test_rejects_negative_sample_rate(self) -> None:
        """Verify that a negative sample rate is rejected."""

        with self.assertRaises(ValueError):
            TimescaleFilter(sample_rate=-1)

    def test_rejects_non_integer_sample_rate(self) -> None:
        """Verify that sample rates must be integers."""

        with self.assertRaises(TypeError):
            TimescaleFilter(sample_rate=48_000.0)  # type: ignore[arg-type]

    def test_rejects_boolean_sample_rate(self) -> None:
        """Verify that booleans are not accepted as sample rates."""

        with self.assertRaises(TypeError):
            TimescaleFilter(sample_rate=True)

    def test_set_speed_updates_speed(self) -> None:
        """Verify that the playback speed can be changed."""

        audio_filter = TimescaleFilter()

        result = audio_filter.set_speed(1.5)

        self.assertIs(result, audio_filter)
        self.assertEqual(audio_filter.speed, 1.5)

    def test_set_speed_preserves_value_after_invalid_update(self) -> None:
        """Verify that an invalid speed does not modify the filter."""

        audio_filter = TimescaleFilter(speed=1.5)

        with self.assertRaises(ValueError):
            audio_filter.set_speed(5.0)

        self.assertEqual(audio_filter.speed, 1.5)

    def test_set_pitch_updates_pitch(self) -> None:
        """Verify that the pitch multiplier can be changed."""

        audio_filter = TimescaleFilter()

        result = audio_filter.set_pitch(1.25)

        self.assertIs(result, audio_filter)
        self.assertEqual(audio_filter.pitch, 1.25)

    def test_set_pitch_preserves_value_after_invalid_update(self) -> None:
        """Verify that an invalid pitch does not modify the filter."""

        audio_filter = TimescaleFilter(pitch=1.25)

        with self.assertRaises(ValueError):
            audio_filter.set_pitch(3.0)

        self.assertEqual(audio_filter.pitch, 1.25)

    def test_set_sample_rate_updates_sample_rate(self) -> None:
        """Verify that the sample rate can be changed."""

        audio_filter = TimescaleFilter()

        result = audio_filter.set_sample_rate(44_100)

        self.assertIs(result, audio_filter)
        self.assertEqual(audio_filter.sample_rate, 44_100)

    def test_set_sample_rate_preserves_value_after_invalid_update(self) -> None:
        """Verify that an invalid sample rate does not modify the filter."""

        audio_filter = TimescaleFilter(sample_rate=48_000)

        with self.assertRaises(ValueError):
            audio_filter.set_sample_rate(0)

        self.assertEqual(audio_filter.sample_rate, 48_000)

    def test_reset_restores_speed_and_pitch(self) -> None:
        """Verify that reset restores default speed and pitch values."""

        audio_filter = TimescaleFilter(
            speed=2.0,
            pitch=1.5,
            sample_rate=44_100,
            enabled=False
        )

        result = audio_filter.reset()

        self.assertIs(result, audio_filter)
        self.assertEqual(audio_filter.speed, 1.0)
        self.assertEqual(audio_filter.pitch, 1.0)
        self.assertEqual(audio_filter.sample_rate, 44_100)
        self.assertFalse(audio_filter.enabled)

    def test_default_configuration_renders_anull(self) -> None:
        """Verify that an unchanged timescale renders a neutral filter."""

        audio_filter = TimescaleFilter()

        self.assertEqual(
            audio_filter.build_expression(),
            "anull"
        )
        self.assertEqual(audio_filter.render(), "anull")

    def test_speed_only_renders_atempo(self) -> None:
        """Verify that a speed change renders an atempo expression."""

        audio_filter = TimescaleFilter(speed=1.5)

        self.assertEqual(
            audio_filter.build_expression(),
            "atempo=1.5"
        )

    def test_minimum_speed_splits_atempo_expression(self) -> None:
        """Verify that very slow playback uses supported tempo factors."""

        audio_filter = TimescaleFilter(speed=0.25)

        self.assertEqual(
            audio_filter.build_expression(),
            "atempo=0.5,atempo=0.5"
        )

    def test_maximum_speed_splits_atempo_expression(self) -> None:
        """Verify that very fast playback uses supported tempo factors."""

        audio_filter = TimescaleFilter(speed=4.0)

        self.assertEqual(
            audio_filter.build_expression(),
            "atempo=2,atempo=2"
        )

    def test_pitch_only_renders_sample_rate_and_tempo_filters(self) -> None:
        """Verify that pitch changes preserve the original playback speed."""

        audio_filter = TimescaleFilter(
            pitch=2.0,
            sample_rate=48_000
        )

        self.assertEqual(
            audio_filter.build_expression(),
            (
                "asetrate=96000,"
                "aresample=48000,"
                "atempo=0.5"
            )
        )

    def test_speed_and_pitch_render_combined_expression(self) -> None:
        """Verify that speed and pitch adjustments are combined."""

        audio_filter = TimescaleFilter(
            speed=2.0,
            pitch=1.25,
            sample_rate=48_000
        )

        self.assertEqual(
            audio_filter.build_expression(),
            (
                "asetrate=60000,"
                "aresample=48000,"
                "atempo=1.6"
            )
        )

    def test_disabled_filter_returns_none(self) -> None:
        """Verify that disabled timescale filters skip rendering."""

        audio_filter = TimescaleFilter(
            speed=2.0,
            enabled=False
        )

        self.assertIsNone(audio_filter.render())
        self.assertEqual(str(audio_filter), "")

if __name__ == "__main__":
    unittest.main()
"""Tests for the WumpiWave custom audio filter."""

from __future__ import annotations

import unittest

from wumpiwave.filters.custom import CustomAudioFilter

class CustomAudioFilterTestCase(unittest.TestCase):
    """Test custom filter configuration, validation, and rendering."""

    def test_creates_filter_with_complete_configuration(self) -> None:
        """Verify that a custom filter preserves its configuration."""

        audio_filter = CustomAudioFilter(
            name="bass boost",
            expression="bass=g=5"
        )

        self.assertEqual(audio_filter.name, "bass boost")
        self.assertEqual(audio_filter.expression, "bass=g=5")
        self.assertTrue(audio_filter.enabled)

    def test_creates_disabled_filter(self) -> None:
        """Verify that a custom filter may initially be disabled."""

        audio_filter = CustomAudioFilter(
            name="bass boost",
            expression="bass=g=5",
            enabled=False
        )

        self.assertFalse(audio_filter.enabled)
        self.assertFalse(audio_filter)

    def test_normalizes_filter_name(self) -> None:
        """Verify that surrounding filter name whitespace is removed."""

        audio_filter = CustomAudioFilter(
            name="  bass boost  ",
            expression="bass=g=5"
        )

        self.assertEqual(audio_filter.name, "bass boost")

    def test_normalizes_expression(self) -> None:
        """Verify that surrounding expression whitespace is removed."""

        audio_filter = CustomAudioFilter(
            name="bass boost",
            expression="  bass=g=5  "
        )

        self.assertEqual(audio_filter.expression, "bass=g=5")

    def test_build_expression_returns_configured_expression(self) -> None:
        """Verify that expression building returns the stored expression."""

        audio_filter = CustomAudioFilter(
            name="bass boost",
            expression="bass=g=5"
        )

        self.assertEqual(
            audio_filter.build_expression(),
            "bass=g=5"
        )

    def test_render_returns_configured_expression(self) -> None:
        """Verify that enabled custom filters render their expression."""

        audio_filter = CustomAudioFilter(
            name="bass boost",
            expression="bass=g=5"
        )

        self.assertEqual(audio_filter.render(), "bass=g=5")
        self.assertEqual(str(audio_filter), "bass=g=5")

    def test_disabled_filter_returns_none(self) -> None:
        """Verify that disabled custom filters skip rendering."""

        audio_filter = CustomAudioFilter(
            name="bass boost",
            expression="bass=g=5",
            enabled=False
        )

        self.assertIsNone(audio_filter.render())
        self.assertEqual(str(audio_filter), "")

    def test_set_expression_updates_expression(self) -> None:
        """Verify that the configured expression can be replaced."""

        audio_filter = CustomAudioFilter(
            name="custom",
            expression="volume=1.5"
        )

        result = audio_filter.set_expression("atempo=1.25")

        self.assertIs(result, audio_filter)
        self.assertEqual(audio_filter.expression, "atempo=1.25")
        self.assertEqual(audio_filter.render(), "atempo=1.25")

    def test_set_expression_normalizes_expression(self) -> None:
        """Verify that replacement expressions are normalized."""

        audio_filter = CustomAudioFilter(
            name="custom",
            expression="volume=1.5"
        )

        audio_filter.set_expression("  atempo=1.25  ")

        self.assertEqual(audio_filter.expression, "atempo=1.25")

    def test_rejects_empty_name(self) -> None:
        """Verify that an empty custom filter name is rejected."""

        with self.assertRaises(ValueError):
            CustomAudioFilter(
                name="",
                expression="volume=1.5"
            )

    def test_rejects_whitespace_name(self) -> None:
        """Verify that a whitespace-only filter name is rejected."""

        with self.assertRaises(ValueError):
            CustomAudioFilter(
                name="   ",
                expression="volume=1.5"
            )

    def test_rejects_non_boolean_enabled_state(self) -> None:
        """Verify that the enabled state must be a boolean."""

        with self.assertRaises(TypeError):
            CustomAudioFilter(
                name="custom",
                expression="volume=1.5",
                enabled=1  # type: ignore[arg-type]
            )

    def test_rejects_non_string_expression(self) -> None:
        """Verify that a custom expression must be a string."""

        with self.assertRaises(TypeError):
            CustomAudioFilter(
                name="custom",
                expression=123  # type: ignore[arg-type]
            )

    def test_rejects_empty_expression(self) -> None:
        """Verify that an empty custom expression is rejected."""

        with self.assertRaises(ValueError):
            CustomAudioFilter(
                name="custom",
                expression=""
            )

    def test_rejects_whitespace_expression(self) -> None:
        """Verify that a whitespace-only expression is rejected."""

        with self.assertRaises(ValueError):
            CustomAudioFilter(
                name="custom",
                expression="   "
            )

    def test_rejects_null_character(self) -> None:
        """Verify that expressions cannot contain null characters."""

        with self.assertRaises(ValueError):
            CustomAudioFilter(
                name="custom",
                expression="volume=1.5\x00"
            )

    def test_rejects_carriage_return(self) -> None:
        """Verify that expressions cannot contain carriage returns."""

        with self.assertRaises(ValueError):
            CustomAudioFilter(
                name="custom",
                expression="volume=1.5\rvolume=2"
            )

    def test_rejects_line_feed(self) -> None:
        """Verify that expressions cannot contain line feeds."""

        with self.assertRaises(ValueError):
            CustomAudioFilter(
                name="custom",
                expression="volume=1.5\nvolume=2"
            )

    def test_invalid_update_preserves_previous_expression(self) -> None:
        """Verify that an invalid update does not modify the filter."""

        audio_filter = CustomAudioFilter(
            name="custom",
            expression="volume=1.5",
        )

        with self.assertRaises(ValueError):
            audio_filter.set_expression("   ")

        self.assertEqual(audio_filter.expression, "volume=1.5")

    def test_non_string_update_preserves_previous_expression(self) -> None:
        """Verify that an invalid expression type preserves configuration."""

        audio_filter = CustomAudioFilter(
            name="custom",
            expression="volume=1.5"
        )

        with self.assertRaises(TypeError):
            audio_filter.set_expression(object())  # type: ignore[arg-type]

        self.assertEqual(audio_filter.expression, "volume=1.5")

if __name__ == "__main__":
    unittest.main()
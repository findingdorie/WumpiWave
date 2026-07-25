"""Tests for the WumpiWave base audio filter."""

from __future__ import annotations

import unittest

from wumpiwave.filters.base import BaseAudioFilter

class StubAudioFilter(BaseAudioFilter):
    """Provide a configurable audio filter for base filter tests.

    Attributes:
        expression:
            The FFmpeg expression returned by the filter.
        build_calls:
            The number of expression build calls.

    Methods:
        build_expression:
            Return the configured FFmpeg expression.
    """

    __slots__ = (
        "build_calls",
        "expression",
    )

    expression: str
    build_calls: int

    def __init__(
        self,
        name: str = "Example",
        expression: str = "volume=1.5",
        *,
        enabled: bool = True
    ) -> None:
        """Initialize the configurable test filter."""

        super().__init__(
            name=name,
            enabled=enabled
        )

        self.expression = expression
        self.build_calls = 0

    def build_expression(self) -> str:
        """Return the configured FFmpeg expression."""

        self.build_calls += 1
        return self.expression

class BaseAudioFilterTestCase(unittest.TestCase):
    """Test base audio filter configuration, state, and rendering."""

    def test_cannot_instantiate_abstract_base_filter(self) -> None:
        """Verify that the abstract base class cannot be instantiated."""

        with self.assertRaises(TypeError):
            BaseAudioFilter("Example")  # type: ignore[abstract]

    def test_creates_enabled_filter(self) -> None:
        """Verify that filters are enabled by default."""

        audio_filter = StubAudioFilter()

        self.assertEqual(audio_filter.name, "Example")
        self.assertTrue(audio_filter.enabled)
        self.assertTrue(audio_filter)

    def test_creates_disabled_filter(self) -> None:
        """Verify that a filter may be disabled during initialization."""

        audio_filter = StubAudioFilter(enabled=False)

        self.assertFalse(audio_filter.enabled)
        self.assertFalse(audio_filter)

    def test_normalizes_filter_name(self) -> None:
        """Verify that surrounding name whitespace is removed."""

        audio_filter = StubAudioFilter(name="  Equalizer  ")

        self.assertEqual(audio_filter.name, "Equalizer")

    def test_rejects_empty_filter_name(self) -> None:
        """Verify that an empty filter name is rejected."""

        with self.assertRaises(ValueError):
            StubAudioFilter(name="")

    def test_rejects_whitespace_filter_name(self) -> None:
        """Verify that a whitespace-only filter name is rejected."""

        with self.assertRaises(ValueError):
            StubAudioFilter(name="   ")

    def test_rejects_non_boolean_initial_state(self) -> None:
        """Verify that initialization requires a boolean state."""

        with self.assertRaises(TypeError):
            StubAudioFilter(
                enabled=1  # type: ignore[arg-type]
            )

    def test_render_returns_expression(self) -> None:
        """Verify that enabled filters render their expression."""

        audio_filter = StubAudioFilter(expression="volume=1.5")

        self.assertEqual(
            audio_filter.render(),
            "volume=1.5"
        )
        self.assertEqual(audio_filter.build_calls, 1)

    def test_render_normalizes_expression(self) -> None:
        """Verify that surrounding expression whitespace is removed."""

        audio_filter = StubAudioFilter(expression="  volume=1.5  ")

        self.assertEqual(
            audio_filter.render(),
            "volume=1.5"
        )

    def test_disabled_filter_does_not_build_expression(self) -> None:
        """Verify that disabled filters skip expression generation."""

        audio_filter = StubAudioFilter(
            expression="volume=1.5",
            enabled=False
        )

        self.assertIsNone(audio_filter.render())
        self.assertEqual(audio_filter.build_calls, 0)

    def test_enable_returns_same_filter(self) -> None:
        """Verify that enabling supports chained configuration."""

        audio_filter = StubAudioFilter(enabled=False)

        result = audio_filter.enable()

        self.assertIs(result, audio_filter)
        self.assertTrue(audio_filter.enabled)
        self.assertTrue(audio_filter)

    def test_disable_returns_same_filter(self) -> None:
        """Verify that disabling supports chained configuration."""

        audio_filter = StubAudioFilter()

        result = audio_filter.disable()

        self.assertIs(result, audio_filter)
        self.assertFalse(audio_filter.enabled)
        self.assertFalse(audio_filter)

    def test_set_enabled_changes_filter_state(self) -> None:
        """Verify that the enabled state can be changed directly."""

        audio_filter = StubAudioFilter()

        disable_result = audio_filter.set_enabled(False)

        self.assertIs(disable_result, audio_filter)
        self.assertFalse(audio_filter.enabled)

        enable_result = audio_filter.set_enabled(True)

        self.assertIs(enable_result, audio_filter)
        self.assertTrue(audio_filter.enabled)

    def test_set_enabled_rejects_non_boolean_value(self) -> None:
        """Verify that state changes require a boolean value."""

        audio_filter = StubAudioFilter()

        with self.assertRaises(TypeError):
            audio_filter.set_enabled(
                "yes"  # type: ignore[arg-type]
            )

        self.assertTrue(audio_filter.enabled)

    def test_string_returns_rendered_expression(self) -> None:
        """Verify that enabled filters stringify to their expression."""

        audio_filter = StubAudioFilter(expression="atempo=1.25")

        self.assertEqual(str(audio_filter), "atempo=1.25")

    def test_disabled_filter_string_is_empty(self) -> None:
        """Verify that disabled filters stringify to an empty string."""

        audio_filter = StubAudioFilter(
            expression="atempo=1.25",
            enabled=False
        )

        self.assertEqual(str(audio_filter), "")
        self.assertEqual(audio_filter.build_calls, 0)

    def test_rejects_empty_expression(self) -> None:
        """Verify that an empty FFmpeg expression is rejected."""

        audio_filter = StubAudioFilter(expression="")

        with self.assertRaises(ValueError):
            audio_filter.render()

    def test_rejects_whitespace_expression(self) -> None:
        """Verify that a whitespace-only expression is rejected."""

        audio_filter = StubAudioFilter(expression="   ")

        with self.assertRaises(ValueError):
            audio_filter.render()

    def test_rejects_null_character(self) -> None:
        """Verify that expressions cannot contain null characters."""

        audio_filter = StubAudioFilter(expression="volume=1.5\x00")

        with self.assertRaises(ValueError):
            audio_filter.render()

    def test_rejects_carriage_return(self) -> None:
        """Verify that expressions cannot contain carriage returns."""

        audio_filter = StubAudioFilter(expression="volume=1.5\rvolume=2")

        with self.assertRaises(ValueError):
            audio_filter.render()

    def test_rejects_line_feed(self) -> None:
        """Verify that expressions cannot contain line feeds."""

        audio_filter = StubAudioFilter(expression="volume=1.5\nvolume=2")

        with self.assertRaises(ValueError):
            audio_filter.render()

    def test_disabled_filter_skips_invalid_expression_validation(
        self
    ) -> None:
        """Verify that disabled filters do not validate expressions."""

        audio_filter = StubAudioFilter(
            expression="",
            enabled=False
        )

        self.assertIsNone(audio_filter.render())
        self.assertEqual(audio_filter.build_calls, 0)

if __name__ == "__main__":
    unittest.main()
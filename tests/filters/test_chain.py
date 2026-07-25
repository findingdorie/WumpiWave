"""Tests for the WumpiWave audio filter chain."""

from __future__ import annotations

import unittest
from typing import cast
from unittest.mock import Mock

from wumpiwave.filters.base import BaseAudioFilter
from wumpiwave.filters.chain import AudioFilterChain

def create_audio_filter(
    name: str,
    expression: str,
    *,
    enabled: bool = True,
) -> BaseAudioFilter:
    """Create a configurable audio filter mock for chain tests."""

    audio_filter = Mock(spec=BaseAudioFilter)
    audio_filter.name = name
    audio_filter.enabled = enabled

    def render() -> str | None:
        """Render the expression while the filter is enabled."""

        if not audio_filter.enabled:
            return None

        return expression

    def enable() -> BaseAudioFilter:
        """Enable the mocked audio filter."""

        audio_filter.enabled = True
        return cast(BaseAudioFilter, audio_filter)

    def disable() -> BaseAudioFilter:
        """Disable the mocked audio filter."""

        audio_filter.enabled = False
        return cast(BaseAudioFilter, audio_filter)

    audio_filter.render.side_effect = render
    audio_filter.enable.side_effect = enable
    audio_filter.disable.side_effect = disable

    return cast(BaseAudioFilter, audio_filter)

class AudioFilterChainTestCase(unittest.TestCase):
    """Test audio filter registration, lookup, state, and rendering."""

    def setUp(self) -> None:
        """Create reusable audio filters for each test."""

        self.equalizer = create_audio_filter(
            "Equalizer",
            "equalizer=f=1000:t=q:w=1:g=3"
        )
        self.timescale = create_audio_filter(
            "Timescale",
            "atempo=1.25"
        )

    def test_creates_empty_chain(self) -> None:
        """Verify that a new chain contains no filters."""

        chain = AudioFilterChain()

        self.assertEqual(chain.names, ())
        self.assertEqual(chain.filters, ())
        self.assertEqual(chain.enabled_filters, ())
        self.assertTrue(chain.is_empty)
        self.assertEqual(len(chain), 0)
        self.assertFalse(chain)

    def test_initializes_with_filters_in_order(self) -> None:
        """Verify that initialization preserves filter order."""

        chain = AudioFilterChain(
            (
                self.equalizer,
                self.timescale
            )
        )

        self.assertEqual(
            chain.names,
            (
                "Equalizer",
                "Timescale"
            )
        )
        self.assertEqual(
            chain.filters,
            (
                self.equalizer,
                self.timescale
            )
        )

    def test_add_registers_filter(self) -> None:
        """Verify that one filter can be added."""

        chain = AudioFilterChain()

        result = chain.add(self.equalizer)

        self.assertIs(result, chain)
        self.assertEqual(chain.filters, (self.equalizer,))
        self.assertEqual(chain.names, ("Equalizer",))

    def test_add_rejects_invalid_value(self) -> None:
        """Verify that non-filter values are rejected."""

        chain = AudioFilterChain()

        with self.assertRaises(TypeError):
            chain.add(object())  # type: ignore[arg-type]

        self.assertTrue(chain.is_empty)

    def test_add_rejects_duplicate_name_case_insensitively(self) -> None:
        """Verify that normalized duplicate names are rejected."""

        duplicate = create_audio_filter(
            "  EQUALIZER  ",
            "volume=2"
        )
        chain = AudioFilterChain((self.equalizer,))

        with self.assertRaises(ValueError):
            chain.add(duplicate)

        self.assertEqual(chain.filters, (self.equalizer,))

    def test_add_rejects_empty_filter_name(self) -> None:
        """Verify that empty filter names are rejected."""

        unnamed_filter = create_audio_filter(
            "   ",
            "volume=2"
        )

        with self.assertRaises(ValueError):
            AudioFilterChain().add(unnamed_filter)

    def test_extend_registers_multiple_filters(self) -> None:
        """Verify that multiple filters can be added together."""

        chain = AudioFilterChain()

        result = chain.extend(
            (
                self.equalizer,
                self.timescale
            )
        )

        self.assertIs(result, chain)
        self.assertEqual(
            chain.filters,
            (
                self.equalizer,
                self.timescale
            )
        )

    def test_extend_is_atomic_for_duplicate_names(self) -> None:
        """Verify that duplicate extension does not partially modify the chain."""

        volume = create_audio_filter(
            "Volume",
            "volume=1.5"
        )
        duplicate = create_audio_filter(
            "equalizer",
            "volume=2"
        )
        chain = AudioFilterChain((self.equalizer,))

        with self.assertRaises(ValueError):
            chain.extend(
                (
                    volume,
                    duplicate
                )
            )

        self.assertEqual(chain.filters, (self.equalizer,))

    def test_extend_is_atomic_for_invalid_values(self) -> None:
        """Verify that invalid extension values do not modify the chain."""

        chain = AudioFilterChain((self.equalizer,))

        with self.assertRaises(TypeError):
            chain.extend(
                (
                    self.timescale,
                    object()
                )
            )

        self.assertEqual(chain.filters, (self.equalizer,))

    def test_get_finds_filter_case_insensitively(self) -> None:
        """Verify that filter lookup ignores casing and whitespace."""

        chain = AudioFilterChain((self.equalizer,))

        result = chain.get("  EQUALIZER  ")

        self.assertIs(result, self.equalizer)

    def test_get_rejects_unknown_filter(self) -> None:
        """Verify that an unknown filter name raises KeyError."""

        chain = AudioFilterChain((self.equalizer,))

        with self.assertRaises(KeyError):
            chain.get("Timescale")

    def test_get_rejects_empty_name(self) -> None:
        """Verify that an empty lookup name is rejected."""

        chain = AudioFilterChain((self.equalizer,))

        with self.assertRaises(ValueError):
            chain.get("   ")

    def test_remove_returns_registered_filter(self) -> None:
        """Verify that removing a filter returns the same instance."""

        chain = AudioFilterChain(
            (
                self.equalizer,
                self.timescale
            )
        )

        removed_filter = chain.remove("EQUALIZER")

        self.assertIs(removed_filter, self.equalizer)
        self.assertEqual(chain.filters, (self.timescale,))

    def test_enable_and_disable_update_filter_state(self) -> None:
        """Verify that registered filters can be enabled and disabled."""

        chain = AudioFilterChain(
            (
                self.equalizer,
                self.timescale
            )
        )

        disable_result = chain.disable("equalizer")

        self.assertIs(disable_result, chain)
        self.assertFalse(self.equalizer.enabled)
        self.assertEqual(
            chain.enabled_filters,
            (self.timescale,)
        )

        enable_result = chain.enable("equalizer")

        self.assertIs(enable_result, chain)
        self.assertTrue(self.equalizer.enabled)
        self.assertEqual(
            chain.enabled_filters,
            (
                self.equalizer,
                self.timescale
            )
        )

    def test_render_combines_enabled_filters_in_order(self) -> None:
        """Verify that enabled expressions are joined in registration order."""

        chain = AudioFilterChain(
            (
                self.equalizer,
                self.timescale
            )
        )

        self.assertEqual(
            chain.render(),
            "equalizer=f=1000:t=q:w=1:g=3,atempo=1.25"
        )

    def test_render_omits_disabled_filters(self) -> None:
        """Verify that disabled filters are excluded from rendering."""

        chain = AudioFilterChain(
            (
                self.equalizer,
                self.timescale
            )
        )
        chain.disable("equalizer")

        self.assertEqual(chain.render(), "atempo=1.25")
        self.assertEqual(str(chain), "atempo=1.25")

    def test_render_returns_none_without_enabled_expression(self) -> None:
        """Verify that no enabled expressions produce None."""

        chain = AudioFilterChain((self.equalizer,))
        chain.disable("equalizer")

        self.assertIsNone(chain.render())
        self.assertEqual(str(chain), "")

    def test_clear_returns_filters_in_previous_order(self) -> None:
        """Verify that clearing returns and removes every filter."""

        chain = AudioFilterChain(
            (
                self.equalizer,
                self.timescale
            )
        )

        removed_filters = chain.clear()

        self.assertEqual(
            removed_filters,
            (
                self.equalizer,
                self.timescale
            )
        )
        self.assertEqual(chain.filters, ())
        self.assertTrue(chain.is_empty)
        self.assertFalse(chain)

    def test_contains_supports_names_and_filter_instances(self) -> None:
        """Verify that membership accepts names and filter objects."""

        chain = AudioFilterChain((self.equalizer,))

        self.assertIn("Equalizer", chain)
        self.assertIn("  EQUALIZER  ", chain)
        self.assertIn(self.equalizer, chain)
        self.assertNotIn("Timescale", chain)
        self.assertNotIn(object(), chain)

    def test_iteration_preserves_registration_order(self) -> None:
        """Verify that iteration follows the rendering order."""

        chain = AudioFilterChain(
            (
                self.equalizer,
                self.timescale
            )
        )

        self.assertEqual(
            tuple(chain),
            (
                self.equalizer,
                self.timescale
            )
        )

if __name__ == "__main__":
    unittest.main()
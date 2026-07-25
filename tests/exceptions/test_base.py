"""Tests for the base WumpiWave exception."""

from __future__ import annotations

import unittest

from wumpiwave.exceptions import WumpiWaveError

class WumpiWaveErrorTestCase(unittest.TestCase):
    """Test the base exception behavior and inheritance."""

    def test_inherits_from_exception(self) -> None:
        """Verify that WumpiWave errors are standard exceptions."""

        self.assertTrue(issubclass(WumpiWaveError, Exception))

    def test_creates_error_without_message(self) -> None:
        """Verify that the exception can be created without arguments."""

        error = WumpiWaveError()

        self.assertEqual(error.args, ())
        self.assertEqual(str(error), "")

    def test_preserves_error_message(self) -> None:
        """Verify that the supplied error message is retained."""

        error = WumpiWaveError("Playback failed.")

        self.assertEqual(error.args, ("Playback failed.",))
        self.assertEqual(str(error), "Playback failed.")

    def test_preserves_multiple_arguments(self) -> None:
        """Verify that multiple exception arguments are retained."""

        error = WumpiWaveError(
            "Playback failed.",
            "connection_lost"
        )

        self.assertEqual(
            error.args,
            (
                "Playback failed.",
                "connection_lost"
            )
        )

    def test_can_be_raised_and_caught(self) -> None:
        """Verify that the exception can be raised and caught directly."""

        with self.assertRaises(WumpiWaveError):
            raise WumpiWaveError("Example error.")

    def test_can_be_caught_as_standard_exception(self) -> None:
        """Verify that the exception can be caught through Exception."""

        with self.assertRaises(Exception):
            raise WumpiWaveError("Example error.")

    def test_supports_custom_subclasses(self) -> None:
        """Verify that specialized exceptions can inherit from the base."""

        class ExampleError(WumpiWaveError):
            """Represent an exception used by this test."""

        error = ExampleError("Example error.")

        self.assertIsInstance(error, WumpiWaveError)
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Example error.")

if __name__ == "__main__":
    unittest.main()
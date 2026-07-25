"""Tests for the WumpiWave backend exceptions."""

from __future__ import annotations

import unittest

from wumpiwave.exceptions import BackendError, WumpiWaveError
from wumpiwave.exceptions.backend import BackendPlaybackError

class BackendExceptionTestCase(unittest.TestCase):
    """Test backend exception inheritance and playback context."""

    def test_backend_error_inherits_from_base_error(self) -> None:
        """Verify that backend errors inherit from WumpiWaveError."""

        self.assertTrue(issubclass(BackendError, WumpiWaveError))

    def test_playback_error_inherits_from_backend_error(self) -> None:
        """Verify that playback errors use the backend hierarchy."""

        self.assertTrue(
            issubclass(
                BackendPlaybackError,
                BackendError
            )
        )

    def test_rejects_missing_operation(self) -> None:
        """Verify that backend playback errors require an operation."""

        with self.assertRaises(TypeError):
            BackendPlaybackError(backend_name="discord")

    def test_preserves_different_backend_operations(self) -> None:
        """Verify that supported operation names remain unchanged."""

        operations = (
            "play",
            "pause",
            "resume",
            "stop",
            "seek",
            "disconnect"
        )

        for operation in operations:
            with self.subTest(operation=operation):
                error = BackendPlaybackError(
                    "Backend operation failed.",
                    operation=operation
                )

                self.assertEqual(error.operation, operation)

    def test_playback_error_can_be_caught_as_backend_error(self) -> None:
        """Verify that playback errors can be handled uniformly."""

        with self.assertRaises(BackendError):
            raise BackendPlaybackError(
                "Playback failed.",
                operation="play"
            )

    def test_playback_error_can_be_caught_as_base_error(self) -> None:
        """Verify that playback errors remain WumpiWave errors."""

        with self.assertRaises(WumpiWaveError):
            raise BackendPlaybackError(
                "Playback failed.",
                operation="play"
            )

if __name__ == "__main__":
    unittest.main()
"""Tests for the WumpiWave exception hierarchy."""

from __future__ import annotations

import unittest

from wumpiwave.exceptions import (
    BackendError,
    PlayerError,
    ProviderError,
    ProviderUnavailableError,
    QueryError,
    QueueError,
    ResolverError,
    WumpiWaveError,
)

class ExceptionHierarchyTestCase(unittest.TestCase):
    """Test inheritance across the WumpiWave exception hierarchy."""

    def test_query_error_inherits_from_base_error(self) -> None:
        """Verify that query errors inherit from WumpiWaveError."""

        self.assertTrue(issubclass(QueryError, WumpiWaveError))

    def test_provider_error_inherits_from_base_error(self) -> None:
        """Verify that provider errors inherit from WumpiWaveError."""

        self.assertTrue(issubclass(ProviderError, WumpiWaveError))

    def test_resolver_error_inherits_from_base_error(self) -> None:
        """Verify that resolver errors inherit from WumpiWaveError."""

        self.assertTrue(issubclass(ResolverError, WumpiWaveError))

    def test_queue_error_inherits_from_base_error(self) -> None:
        """Verify that queue errors inherit from WumpiWaveError."""

        self.assertTrue(issubclass(QueueError, WumpiWaveError))

    def test_backend_error_inherits_from_base_error(self) -> None:
        """Verify that backend errors inherit from WumpiWaveError."""

        self.assertTrue(issubclass(BackendError, WumpiWaveError))

    def test_player_error_inherits_from_base_error(self) -> None:
        """Verify that player errors inherit from WumpiWaveError."""

        self.assertTrue(issubclass(PlayerError, WumpiWaveError))

    def test_provider_unavailable_error_inherits_from_provider_error(
        self,
    ) -> None:
        """Verify that unavailable providers use the provider hierarchy."""

        self.assertTrue(
            issubclass(
                ProviderUnavailableError,
                ProviderError
            )
        )

    def test_provider_unavailable_error_is_not_query_error(self) -> None:
        """Verify that provider availability is not classified as a query error."""

        self.assertFalse(
            issubclass(
                ProviderUnavailableError,
                QueryError
            )
        )

    def test_specialized_errors_can_be_caught_by_base_error(self) -> None:
        """Verify that specialized errors can be caught uniformly."""

        errors = (
            QueryError("Query failed."),
            ProviderError("Provider failed."),
            ResolverError("Resolver failed."),
            QueueError("Queue failed."),
            BackendError("WumpiWaveBackend", "Backend failed."),
            PlayerError("Player failed.")
        )

        for error in errors:
            with self.subTest(error_type=type(error).__name__):
                self.assertIsInstance(error, WumpiWaveError)
                self.assertIsInstance(error, Exception)

if __name__ == "__main__":
    unittest.main()
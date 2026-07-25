"""Tests for the public WumpiWave package interface."""

from __future__ import annotations

import unittest
from inspect import isclass

import wumpiwave
from wumpiwave import WumpiWaveClient, __version__

class PackageTestCase(unittest.TestCase):
    """Test package metadata and public root exports."""

    def test_version_is_string(self) -> None:
        """Verify that the package version is exposed as a string."""

        self.assertIsInstance(__version__, str)

    def test_version_is_not_empty(self) -> None:
        """Verify that the exposed package version is not empty."""

        self.assertTrue(__version__.strip())

    def test_client_is_exposed_from_package_root(self) -> None:
        """Verify that the main client is available from the package root."""

        self.assertIs(wumpiwave.WumpiWaveClient, WumpiWaveClient)

    def test_client_export_is_class(self) -> None:
        """Verify that the exported client is a class."""

        self.assertTrue(isclass(WumpiWaveClient))

    def test_public_exports_include_client(self) -> None:
        """Verify that the main client is included in the public API."""

        self.assertIn("WumpiWaveClient", wumpiwave.__all__)

    def test_public_exports_include_version(self) -> None:
        """Verify that the package version is included in the public API."""

        self.assertIn("__version__", wumpiwave.__all__)

    def test_public_exports_do_not_contain_duplicates(self) -> None:
        """Verify that public package exports are unique."""

        self.assertEqual(
            len(wumpiwave.__all__),
            len(set(wumpiwave.__all__))
        )

if __name__ == "__main__":
    unittest.main()
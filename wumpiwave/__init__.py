from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

"""
WumpiWave
=========

An asynchronous media player library designed for Discord applications.

WumpiWave provides a unified media model, metadata providers, stream
resolvers, queue management, audio playback, event handling, and Discord
voice integration.

The public API of the library is exposed directly through this package.
Library users should normally import classes and functions from
``wumpiwave`` instead of accessing internal modules.

Attributes:
    __version__:
        The currently installed version of the WumpiWave package.

Methods:
    None
"""

try:
    __version__: str = version("wuumpiwave")
except PackageNotFoundError:
    __version__ = "0.1.0.dev0"

__all__: tuple[str, ...] = (
    "__version__",
)
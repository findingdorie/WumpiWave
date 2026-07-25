"""Public interface for the WumpiWave package.

WumpiWave is an asynchronous media-player library designed for Discord
applications. Public classes, models, exceptions, and utilities are exported
through this package as they become available.

Attributes:
    __version__:
        The installed version of the WumpiWave package.

Methods:
    None
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from .client import WumpiWaveClient

try:
    __version__: str = version("wumpiwave")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__: tuple[str, ...] = (
    "__version__",
    "WumpiWaveClient"
)

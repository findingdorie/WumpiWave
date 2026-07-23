"""
Base exceptions used throughout WumpiWave.

This module defines the root exception inherited by every public exception
raised by the WumpiWave library.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

class WumpiWaveError(Exception):
    """
    Represents the base exception for all WumpiWave errors.

    Catching this exception allows library users to handle every error raised
    intentionally by WumpiWave without catching unrelated Python exceptions.

    Attributes:
        None

    Methods:
        None
    """

    __slots__ = ()

__all__: tuple[str, ...] = (
    "WumpiWaveError",
)
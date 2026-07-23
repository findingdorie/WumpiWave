"""
Base exceptions used throughout WumpiWave.

This module defines the root exception inherited by every custom exception
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

    Catching this exception allows library consumers to handle every custom
    error raised by WumpiWave without also catching unrelated built-in
    exceptions.

    Attributes:
        None

    Methods:
        None
    """

__all__: tuple[str, ...] = (
    "WumpiWaveError",
)
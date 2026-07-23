"""
Base exceptions used throughout WumpiWave.

This module provides the root exception class inherited by every public
exception raised by the library.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

class WumpiWaveError(Exception):
    """
    Represents the base exception for all WumpiWave errors.

    Catching this exception allows library consumers to handle every error
    raised directly by WumpiWave without catching unrelated Python exceptions.

    Attributes:
        - message:
            The human-readable description of the error.

    Methods:
        __init__:
            Initializes the exception with a human-readable message.
    """

    def __init__(self, provider_name: str, message: str) -> None:
        """
        Initialize a new WumpiWave exception.

        Args:
            message:
                The human-readable description of the error.
        """

        self.message: str = message
        super().__init__(message)

__all__: tuple[str, ...] = (
    "WumpiWaveError",
)
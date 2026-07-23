"""Playback queue exceptions raised throughout WumpiWave.

This module defines errors related to empty queues, invalid queue positions,
and missing queue entries.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .base import WumpiWaveError


class QueueError(WumpiWaveError):
    """Represents the base exception for playback queue errors.

    Attributes:
        None

    Methods:
        None
    """

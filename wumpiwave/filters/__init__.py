"""Audio filters available in WumpiWave.

This package contains FFmpeg-compatible audio filters and filter chain
components used to transform media during playback.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .base import BaseAudioFilter
from .chain import AudioFilterChain
from .custom import CustomAudioFilter
from .equalizer import EqualizerBand, EqualizerFilter
from .timescale import TimescaleFilter

__all__: tuple[str, ...] = (
    "AudioFilterChain",
    "BaseAudioFilter",
    "CustomAudioFilter",
    "EqualizerBand",
    "EqualizerFilter",
    "TimescaleFilter",
)
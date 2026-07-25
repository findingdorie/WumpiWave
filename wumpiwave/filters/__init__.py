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

__all__: tuple[str, ...] = ("BaseAudioFilter",)
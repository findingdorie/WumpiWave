"""Playback backends available in WumpiWave.

This package contains backend implementations responsible for delivering
resolved media sources to external playback systems such as Discord voice
connections through FFmpeg.

Backends consume source-independent WumpiWave playback models and must not
perform metadata queries or stream resolution themselves.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .base import BasePlaybackBackend
from .discord import DiscordVoiceBackend
from .ffmpeg import DiscordPCMSource, FFmpegAudioSourceFactory

__all__: tuple[str, ...] = (
    "BasePlaybackBackend",
    "DiscordPCMSource",
    "DiscordVoiceBackend",
    "FFmpegAudioSourceFactory",
)
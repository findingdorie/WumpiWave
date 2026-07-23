"""
Enumerations shared across the WumpiWave media system.

This module defines stable string-based values used by media models, queries,
queues, playback states, loop behavior, and track lifecycle events.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from enum import StrEnum, unique

@unique
class MediaSource(StrEnum):
    """
    Represents the original platform or source of a media item.

    Attributes:
        - YOUTUBE:
            Media metadata originating from YouTube.
        - SPOTIFY:
            Media metadata originating from Spotify.
        - HTTP:
            Media loaded directly from an HTTP or HTTPS resource.
        - UNKNOWN:
            Media whose original source could not be identified.

    Methods:
        None
    """

    YOUTUBE = "youtube"
    SPOTIFY = "spotify"
    HTTP = "http"
    UNKNOWN = "unknown"

@unique
class MediaType(StrEnum):
    """
    Represents the type of a media resource.

    Attributes:
        - TRACK:
            A single playable media item.
        - PLAYLIST:
            An ordered collection of media tracks.
        - ALBUM:
            A collection of tracks published as one album.

    Methods:
        None
    """

    TRACK = "track"
    PLAYLIST = "playlist"
    ALBUM = "album"

@unique
class QueryType(StrEnum):
    """
    Represents the format of a submitted media query.

    Attributes:
        - SEARCH:
            A text-based search query that requires provider lookup.
        - URL:
            A direct URL pointing to a supported media resource.

    Methods:
        None
    """

    SEARCH = "search"
    URL = "url"

@unique
class LoopMode(StrEnum):
    """
    Represents the active playback loop behavior.

    Attributes:
        - OFF:
            Playback continues without repeating tracks.
        - TRACK:
            The currently playing track repeats until the mode changes.
        - QUEUE:
            Finished tracks return to the end of the queue.

    Methods:
        None
    """

    OFF = "off"
    TRACK = "track"
    QUEUE = "queue"

@unique
class PlayerState(StrEnum):
    """
    Represents the current lifecycle state of a media player.

    Attributes:
        - IDLE:
            The player is active but has no current track.
        - BUFFERING:
            The player is preparing or resolving a playable source.
        - PLAYING:
            The player is currently playing audio.
        - PAUSED:
            Playback is temporarily paused.
        - STOPPED:
            Playback was stopped explicitly.
        - DESTROYED:
            The player has been permanently closed and cannot be reused.

    Methods:
        None
    """

    IDLE = "idle"
    BUFFERING = "buffering"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    DESTROYED = "destroyed"

@unique
class TrackEndReason(StrEnum):
    """
    Represents the reason why playback of a track ended.

    Attributes:
        - FINISHED:
            The track reached its natural end.
        - STOPPED:
            Playback was stopped explicitly.
        - SKIPPED:
            The track was skipped by a player action.
        - REPLACED:
            The track was replaced by another track.
        - ERROR:
            Playback ended because an exception occurred.

    Methods:
        None
    """

    FINISHED = "finished"
    STOPPED = "stopped"
    SKIPPED = "skipped"
    REPLACED = "replaced"
    ERROR = "error"

__all__: tuple[str, ...] = (
    "LoopMode",
    "MediaSource",
    "MediaType",
    "PlayerState",
    "QueryType",
    "TrackEndReason"
)
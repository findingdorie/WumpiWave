"""Playback backend protocol used throughout WumpiWave.

This module defines the structural interface required for playback backends
that consume resolved audio sources and control their playback lifecycle.

Attributes:
    PlaybackCompletionCallback:
        A callback invoked when playback finishes or fails.

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from ..models import PlayableSource

type PlaybackCompletionCallback = Callable[[Exception | None], None]

@runtime_checkable
class PlaybackBackend(Protocol):
    """Define the interface required for playback backends.

    A playback backend consumes resolved audio sources and controls the actual
    audio output. Implementations may integrate with Discord voice clients or
    other audio systems without requiring inheritance from a concrete class.

    Attributes:
        name:
            The unique public name used to identify the backend.
        connected:
            Whether the backend currently has an active connection.
        playing:
            Whether the backend is currently playing audio.
        paused:
            Whether the backend currently has paused audio.

    Methods:
        play:
            Start playing a resolved audio source.
        pause:
            Temporarily pause the current audio source.
        resume:
            Resume the currently paused audio source.
        stop:
            Stop the current audio source.
        disconnect:
            Close the active backend connection.
    """

    @property
    def name(self) -> str:
        """Return the unique public name of the backend.

        Returns:
            The backend name used for identification and error reporting.
        """

        ...

    @property
    def connected(self) -> bool:
        """Return whether the backend has an active connection.

        Returns:
            ``True`` when the backend is connected, otherwise ``False``.
        """

        ...

    @property
    def playing(self) -> bool:
        """Return whether the backend is currently playing audio.

        Returns:
            ``True`` while audio is playing, otherwise ``False``.
        """

        ...

    @property
    def paused(self) -> bool:
        """Return whether the backend currently has paused audio.

        Returns:
            ``True`` while audio is paused, otherwise ``False``.
        """

        ...

    async def play(
        self,
        source: PlayableSource,
        *,
        start_position: float = 0.0,
        on_complete: PlaybackCompletionCallback | None = None,
    ) -> None:
        """Start playing a resolved audio source.

        Args:
            source:
                The resolved audio source to play.
            start_position:
                The position in seconds from which playback should begin.
            on_complete:
                The callback invoked when playback finishes or fails. The
                callback receives ``None`` after successful playback or the
                exception that interrupted playback.

        Raises:
            BackendConnectionError:
                The backend does not have an active connection.
            BackendPlaybackError:
                The backend could not start playback.
            ValueError:
                The supplied start position is invalid.
        """

        ...

    async def pause(self) -> None:
        """Temporarily pause the current audio source.

        Raises:
            BackendConnectionError:
                The backend does not have an active connection.
            BackendPlaybackError:
                The backend could not pause playback.
        """

        ...

    async def resume(self) -> None:
        """Resume the currently paused audio source.

        Raises:
            BackendConnectionError:
                The backend does not have an active connection.
            BackendPlaybackError:
                The backend could not resume playback.
        """

        ...

    async def stop(self) -> None:
        """Stop the current audio source.

        Calling this method while no audio is active should not raise an
        exception.

        Raises:
            BackendPlaybackError:
                The backend could not stop playback.
        """

        ...

    async def disconnect(self) -> None:
        """Close the active backend connection.

        Calling this method more than once should not raise an exception.

        Raises:
            BackendConnectionError:
                The backend connection could not be closed cleanly.
        """

        ...


__all__: tuple[str, ...] = (
    "PlaybackBackend",
    "PlaybackCompletionCallback"
)
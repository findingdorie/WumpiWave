"""Media player protocol used throughout WumpiWave.

This module defines the structural interface required for media players that
manage queues, control playback, and coordinate playback backends.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from ..models import (
    LoopMode,
    MediaTrack,
    PlayerState,
    QueueEntry,
)
from .backend import PlaybackBackend
from .dispatcher import EventDispatcher

@runtime_checkable
class MediaPlayer(Protocol):
    """Define the interface required for media players.

    A media player manages queued tracks, playback state, loop behavior,
    playback history, volume, and communication with a playback backend.
    Implementations do not need to inherit from this protocol as long as they
    provide the required attributes and methods.

    Attributes:
        identifier:
            The unique numeric identifier assigned to the player.
        backend:
            The playback backend used to output audio.
        dispatcher:
            The event dispatcher used to emit playback events.
        state:
            The current lifecycle and playback state.
        loop_mode:
            The active track or queue loop behavior.
        volume:
            The current playback volume multiplier.
        position:
            The estimated current playback position in seconds.
        current:
            The queue entry currently being played, when available.
        queue:
            An immutable snapshot of the pending playback queue.
        history:
            An immutable snapshot of previously played queue entries.
        playing:
            Whether the player is currently playing audio.
        paused:
            Whether the player currently has paused audio.
        destroyed:
            Whether the player has been permanently destroyed.

    Methods:
        enqueue:
            Add one media track to the playback queue.
        enqueue_many:
            Add multiple media tracks to the playback queue.
        play:
            Start playback using the current or next queued entry.
        pause:
            Temporarily pause the current track.
        resume:
            Resume the currently paused track.
        stop:
            Stop the current track and optionally clear the queue.
        skip:
            Skip the current track and continue playback.
        previous:
            Return to the previously played queue entry.
        seek:
            Move playback to a specific position in the current track.
        shuffle:
            Randomize the order of pending queue entries.
        set_loop:
            Change the active playback loop mode.
        set_volume:
            Change the playback volume multiplier.
        remove:
            Remove a queue entry by its current index.
        move:
            Move a queue entry to another index.
        clear:
            Remove all pending queue entries.
        disconnect:
            Disconnect the playback backend.
        destroy:
            Permanently close the player and release its resources.
    """

    @property
    def identifier(self) -> int:
        """Return the unique player identifier.

        Returns:
            The numeric identifier assigned to the player.
        """

        ...

    @property
    def backend(self) -> PlaybackBackend:
        """Return the playback backend used by the player.

        Returns:
            The configured playback backend.
        """

        ...

    @property
    def dispatcher(self) -> EventDispatcher:
        """Return the event dispatcher used by the player.

        Returns:
            The configured playback event dispatcher.
        """

        ...

    @property
    def state(self) -> PlayerState:
        """Return the current player state.

        Returns:
            The active lifecycle and playback state.
        """

        ...

    @property
    def loop_mode(self) -> LoopMode:
        """Return the active playback loop mode.

        Returns:
            The configured track or queue loop behavior.
        """

        ...

    @property
    def volume(self) -> float:
        """Return the current playback volume.

        Returns:
            The active volume multiplier.
        """

        ...

    @property
    def position(self) -> float:
        """Return the estimated playback position.

        Returns:
            The current playback position in seconds.
        """

        ...

    @property
    def current(self) -> QueueEntry | None:
        """Return the current queue entry.

        Returns:
            The active queue entry, or ``None`` when nothing is playing.
        """

        ...

    @property
    def queue(self) -> tuple[QueueEntry, ...]:
        """Return a snapshot of the pending playback queue.

        Returns:
            The pending queue entries in playback order.
        """

        ...

    @property
    def history(self) -> tuple[QueueEntry, ...]:
        """Return a snapshot of the playback history.

        Returns:
            Previously played queue entries in chronological order.
        """

        ...

    @property
    def playing(self) -> bool:
        """Return whether the player is currently playing audio.

        Returns:
            ``True`` while audio is playing, otherwise ``False``.
        """

        ...

    @property
    def paused(self) -> bool:
        """Return whether the player currently has paused audio.

        Returns:
            ``True`` while audio is paused, otherwise ``False``.
        """

        ...

    @property
    def destroyed(self) -> bool:
        """Return whether the player has been destroyed.

        Returns:
            ``True`` when the player can no longer be reused.
        """

        ...

    async def enqueue(
        self,
        track: MediaTrack,
        *,
        requester_id: int | None = None,
        start_position: float = 0.0,
    ) -> QueueEntry:
        """Add one media track to the playback queue.

        Args:
            track:
                The normalized media track to queue.
            requester_id:
                The Discord user identifier of the requester, when available.
            start_position:
                The position in seconds from which playback should begin.

        Returns:
            The queue entry created for the supplied track.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            ValueError:
                The requester identifier or start position is invalid.
        """

        ...

    async def enqueue_many(
        self,
        tracks: Iterable[MediaTrack],
        *,
        requester_id: int | None = None,
    ) -> tuple[QueueEntry, ...]:
        """Add multiple media tracks to the playback queue.

        Args:
            tracks:
                The normalized media tracks to queue in iteration order.
            requester_id:
                The Discord user identifier assigned to every created entry,
                when available.

        Returns:
            The queue entries created for the supplied tracks.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            ValueError:
                The requester identifier is invalid.
        """

        ...

    async def play(self) -> QueueEntry:
        """Start playback using the current or next queued entry.

        Returns:
            The queue entry whose playback was started.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            QueueEmptyError:
                No current or pending queue entry is available.
            InvalidPlayerStateError:
                Playback cannot begin in the current player state.
            ResolverError:
                The current track could not be resolved.
            BackendError:
                The backend could not start playback.
        """

        ...

    async def pause(self) -> None:
        """Temporarily pause the current track.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            NoCurrentTrackError:
                The player does not have a current track.
            InvalidPlayerStateError:
                Playback cannot be paused in the current state.
            BackendError:
                The backend could not pause playback.
        """

        ...

    async def resume(self) -> None:
        """Resume the currently paused track.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            NoCurrentTrackError:
                The player does not have a current track.
            InvalidPlayerStateError:
                Playback cannot resume in the current state.
            BackendError:
                The backend could not resume playback.
        """

        ...

    async def stop(self, *, clear_queue: bool = False) -> QueueEntry | None:
        """Stop the current track.

        Args:
            clear_queue:
                Whether all pending queue entries should also be removed.

        Returns:
            The queue entry that was stopped, or ``None`` when no track was
            active.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            BackendError:
                The backend could not stop playback.
        """

        ...

    async def skip(self) -> QueueEntry:
        """Skip the current track and continue playback.

        Returns:
            The queue entry that was skipped.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            NoCurrentTrackError:
                The player does not have a current track.
            BackendError:
                The backend could not stop the current track.
        """

        ...

    async def previous(self) -> QueueEntry:
        """Return to the previously played queue entry.

        Returns:
            The previous queue entry selected for playback.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            QueueEmptyError:
                The playback history does not contain a previous entry.
            BackendError:
                The backend could not replace the current track.
        """

        ...

    async def seek(self, position: float) -> None:
        """Move playback to a position in the current track.

        Args:
            position:
                The target playback position in seconds.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            NoCurrentTrackError:
                The player does not have a current track.
            InvalidPlayerStateError:
                Seeking is unavailable in the current player state.
            UnsupportedMediaError:
                The current audio source does not support seeking.
            ValueError:
                The supplied position is invalid.
        """

        ...

    async def shuffle(self) -> None:
        """Randomize the order of pending queue entries.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
        """

        ...

    async def set_loop(self, loop_mode: LoopMode) -> None:
        """Change the active playback loop mode.

        Args:
            loop_mode:
                The loop behavior that should become active.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
        """

        ...

    async def set_volume(self, volume: float) -> None:
        """Change the playback volume multiplier.

        Args:
            volume:
                The new finite volume multiplier.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            ValueError:
                The supplied volume is invalid.
        """

        ...

    async def remove(self, index: int) -> QueueEntry:
        """Remove a queue entry by its current index.

        Args:
            index:
                The zero-based index of the queue entry to remove.

        Returns:
            The removed queue entry.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            QueueIndexOutOfRangeError:
                The supplied queue index does not exist.
        """

        ...

    async def move(self, current_index: int, target_index: int) -> None:
        """Move a queue entry to another index.

        Args:
            current_index:
                The current zero-based index of the queue entry.
            target_index:
                The zero-based destination index.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            QueueIndexOutOfRangeError:
                One of the supplied indexes does not exist.
        """

        ...

    async def clear(self) -> tuple[QueueEntry, ...]:
        """Remove every pending queue entry.

        Returns:
            The queue entries removed in their previous playback order.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
        """

        ...

    async def disconnect(self) -> None:
        """Disconnect the playback backend.

        Calling this method more than once should not raise an exception.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            BackendError:
                The backend could not disconnect cleanly.
        """

        ...

    async def destroy(self) -> None:
        """Permanently close the player and release its resources.

        Calling this method more than once should not raise an exception.

        Raises:
            BackendError:
                The playback backend could not be closed cleanly.
            ExceptionGroup:
                Multiple cleanup operations failed.
        """

        ...

__all__: tuple[str, ...] = ("MediaPlayer",)
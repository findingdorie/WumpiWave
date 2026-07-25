"""Default media player implementation used by WumpiWave.

This module coordinates playback queues, stream resolution, playback backends,
loop modes, playback history, seeking, player state, and playback events.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

import logging
from asyncio import CancelledError, Lock, Task
from collections.abc import Iterable
from math import isfinite
from time import monotonic

from ..events import PlaybackEventDispatcher
from ..exceptions import (
    InvalidPlayerStateError,
    NoCurrentTrackError,
    PlayerDestroyedError,
    QueueEmptyError,
)
from ..models import (
    LoopMode,
    MediaTrack,
    PlaybackEvent,
    PlayerDestroyEvent,
    PlayerState,
    PlayerStateChangeEvent,
    PlayableSource,
    QueueEmptyEvent,
    QueueEntry,
    TrackEndEvent,
    TrackEndReason,
    TrackStartEvent,
)
from ..protocols import EventDispatcher, PlaybackBackend
from ..resolvers import ResolverRegistry
from .queue import PlaybackQueue

_logger: logging.Logger = logging.getLogger(__name__)

class WumpiWavePlayer:
    """Coordinate media resolution, queue management, and audio playback.

    The player retrieves queue entries in playback order, resolves their media
    tracks into playable sources, sends those sources to a playback backend,
    and dispatches lifecycle events to registered listeners.

    Playback history is maintained independently from the active queue. Looping
    the current track replays the same entry, while queue looping appends
    completed entries to the end of the queue.

    Attributes:
        identifier:
            The numeric identifier associated with the player.
        backend:
            The backend responsible for delivering resolved audio.
        dispatcher:
            The dispatcher responsible for delivering playback events.
        resolvers:
            The registry responsible for resolving media tracks.
        state:
            The current player state.
        loop_mode:
            The currently configured playback loop mode.
        volume:
            The current playback volume.
        position:
            The estimated playback position in seconds.
        current:
            The currently active queue entry, when available.
        queue:
            An immutable snapshot of queued entries.
        history:
            An immutable snapshot of previously played entries.
        playing:
            Whether the player is actively playing audio.
        paused:
            Whether playback is currently paused.
        destroyed:
            Whether the player has released its resources.

    Methods:
        enqueue:
            Add one media track to the playback queue.
        enqueue_many:
            Add multiple media tracks to the playback queue.
        play:
            Start the first queued track.
        pause:
            Pause active playback.
        resume:
            Resume paused playback.
        stop:
            Stop active playback and optionally clear the queue.
        skip:
            Stop the current track and start the next queued track.
        previous:
            Return to the most recently played track.
        seek:
            Restart the current track from another playback position.
        shuffle:
            Randomize the order of queued entries.
        set_loop:
            Change the active loop mode.
        set_volume:
            Change the current playback volume.
        remove:
            Remove one queued entry by index.
        move:
            Move a queued entry to another index.
        clear:
            Remove every queued entry.
        disconnect:
            Stop playback and disconnect the backend.
        destroy:
            Release all resources owned by the player.
        _start_entry:
            Resolve and begin playing one queue entry.
        _terminate_current:
            Stop and finalize the current queue entry.
        _start_next:
            Start the next queued entry or dispatch a queue-empty event.
        _handle_backend_completion:
            Process natural playback completion and playback errors.
        _change_state:
            Change the player state and append a state event.
        _dispatch_events:
            Dispatch playback events in their original order.
        _prepend:
            Insert an entry at the beginning of the playback queue.
        _append_history:
            Add an entry to playback history.
        _validate_position:
            Validate a playback position.
        _validate_volume:
            Validate a playback volume.
        _ensure_active:
            Ensure that the player has not been destroyed.
        _consume_completion_task:
            Consume and log asynchronous completion failures.
    """

    __slots__ = (
        "_backend",
        "_close_resolvers",
        "_current",
        "_current_source",
        "_destroyed",
        "_dispatcher",
        "_history",
        "_history_limit",
        "_identifier",
        "_lock",
        "_loop_mode",
        "_playback_generation",
        "_position_offset",
        "_queue",
        "_resolvers",
        "_started_at",
        "_state",
        "_volume",
    )

    _backend: PlaybackBackend
    _close_resolvers: bool
    _current: QueueEntry | None
    _current_source: PlayableSource | None
    _destroyed: bool
    _dispatcher: EventDispatcher
    _history: list[QueueEntry]
    _history_limit: int
    _identifier: int
    _lock: Lock
    _loop_mode: LoopMode
    _playback_generation: int
    _position_offset: float
    _queue: PlaybackQueue
    _resolvers: ResolverRegistry
    _started_at: float | None
    _state: PlayerState
    _volume: float

    def __init__(
            self,
            identifier: int,
            backend: PlaybackBackend,
            resolvers: ResolverRegistry,
            *,
            dispatcher: EventDispatcher | None = None,
            queue: PlaybackQueue | None = None,
            loop_mode: LoopMode = LoopMode.OFF,
            volume: float = 1.0,
            history_limit: int = 100,
            close_resolvers: bool = False,
    ) -> None:
        """Initialize a WumpiWave media player.

        Args:
            identifier:
                The numeric identifier associated with the player.
            backend:
                The playback backend used to deliver resolved audio.
            resolvers:
                The registry used to resolve media tracks.
            dispatcher:
                An optional playback event dispatcher.
            queue:
                An optional existing playback queue.
            loop_mode:
                The initial playback loop mode.
            volume:
                The initial non-negative playback volume.
            history_limit:
                The maximum number of entries retained in playback history.
            close_resolvers:
                Whether destroying the player also closes its resolver registry.

        Raises:
            TypeError:
                The player identifier is not an integer or is a boolean.
            ValueError:
                The volume or history limit is invalid.
        """

        if isinstance(identifier, bool) or not isinstance(identifier, int):
            raise TypeError("The media player identifier must be an integer.")

        if isinstance(history_limit, bool) or history_limit < 0:
            raise ValueError("The playback history limit must be a non-negative integer.")

        self._identifier = identifier
        self._backend = backend
        self._resolvers = resolvers
        self._dispatcher = dispatcher or PlaybackEventDispatcher()
        self._queue = queue or PlaybackQueue()
        self._history = []
        self._history_limit = history_limit
        self._loop_mode = loop_mode
        self._volume = self._validate_volume(volume)
        self._state = PlayerState.IDLE
        self._current = None
        self._current_source = None
        self._position_offset = 0.0
        self._started_at = None
        self._playback_generation = 0
        self._close_resolvers = close_resolvers
        self._destroyed = False
        self._lock = Lock()

    @property
    def identifier(self) -> int:
        """Return the numeric player identifier.

        Returns:
            The identifier associated with the player.
        """

        return self._identifier

    @property
    def backend(self) -> PlaybackBackend:
        """Return the playback backend.

        Returns:
            The backend used to deliver resolved audio.
        """

        return self._backend

    @property
    def dispatcher(self) -> EventDispatcher:
        """Return the playback event dispatcher.

        Returns:
            The configured asynchronous event dispatcher.
        """

        return self._dispatcher

    @property
    def resolvers(self) -> ResolverRegistry:
        """Return the stream resolver registry.

        Returns:
            The registry used to resolve media tracks.
        """

        return self._resolvers

    @property
    def state(self) -> PlayerState:
        """Return the current player state.

        Returns:
            The current playback lifecycle state.
        """

        return self._state

    @property
    def loop_mode(self) -> LoopMode:
        """Return the active playback loop mode.

        Returns:
            The currently configured loop mode.
        """

        return self._loop_mode

    @property
    def volume(self) -> float:
        """Return the current playback volume.

        Returns:
            The configured non-negative volume.
        """

        return self._volume

    @property
    def position(self) -> float:
        """Return the estimated current playback position.

        Returns:
            The playback position in seconds.
        """

        if self._current is None:
            return 0.0

        playback_position: float = self._position_offset

        if (
            self._state is PlayerState.PLAYING
            and self._started_at is not None
        ):
            playback_position += monotonic() - self._started_at

        duration: float | None = self._current.track.duration

        if duration is not None:
            return min(playback_position, duration)

        return playback_position

    @property
    def current(self) -> QueueEntry | None:
        """Return the currently active queue entry.

        Returns:
            The active entry, or ``None`` when no track is selected.
        """

        return self._current

    @property
    def queue(self) -> tuple[QueueEntry, ...]:
        """Return an immutable queue snapshot.

        Returns:
            The queued entries in their current playback order.
        """

        return self._queue.entries

    @property
    def history(self) -> tuple[QueueEntry, ...]:
        """Return an immutable playback history snapshot.

        Returns:
            Previously completed entries in chronological order.
        """

        return tuple(self._history)

    @property
    def playing(self) -> bool:
        """Return whether the player is actively playing.

        Returns:
            ``True`` when the player state is playing.
        """

        return self._state is PlayerState.PLAYING

    @property
    def paused(self) -> bool:
        """Return whether playback is paused.

        Returns:
            ``True`` when the player state is paused.
        """

        return self._state is PlayerState.PAUSED

    @property
    def destroyed(self) -> bool:
        """Return whether the player has been destroyed.

        Returns:
            ``True`` when player resources have been released.
        """

        return self._destroyed

    def enqueue(
        self,
        track: MediaTrack,
        *,
        requester_id: int | None = None,
        start_position: float = 0.0,
    ) -> QueueEntry:
        """Add one media track to the playback queue.

        Args:
            track:
                The normalized media track to enqueue.
            requester_id:
                The optional identifier of the requesting user.
            start_position:
                The initial playback position in seconds.

        Returns:
            The newly created queue entry.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            ValueError:
                The requester identifier or position is invalid.
        """

        self._ensure_active()

        return self._queue.add(
            track,
            requester_id=requester_id,
            start_position=start_position
        )

    def enqueue_many(
        self,
        tracks: Iterable[MediaTrack],
        *,
        requester_id: int | None = None,
        start_position: float = 0.0,
    ) -> tuple[QueueEntry, ...]:
        """Add multiple media tracks to the playback queue.

        Args:
            tracks:
                The normalized media tracks to enqueue.
            requester_id:
                The optional identifier assigned to every created entry.
            start_position:
                The initial position assigned to every created entry.

        Returns:
            The newly created entries in their input order.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            ValueError:
                The requester identifier or position is invalid.
        """

        self._ensure_active()

        entries: tuple[QueueEntry, ...] = tuple(
            QueueEntry(
                track=track,
                requester_id=requester_id,
                start_position=start_position
            )
            for track in tracks
        )
        self._queue.extend(entries)

        return entries

    async def play(self) -> None:
        """Start the current or first queued media track.

        Paused playback is resumed automatically. Calling this method while
        already playing or buffering raises an invalid-state exception.

        Raises:
            InvalidPlayerStateError:
                Playback is already active.
            PlayerDestroyedError:
                The player has already been destroyed.
            QueueEmptyError:
                No media track is available for playback.
            ResolverError:
                The selected track could not be resolved.
            BackendError:
                The backend could not begin playback.
        """

        self._ensure_active()

        if self._state is PlayerState.PAUSED:
            return await self.resume()

        events: list[PlaybackEvent] = []

        try:
            async with self._lock:
                if self._state in {
                    PlayerState.BUFFERING,
                    PlayerState.PLAYING
                }:
                    raise InvalidPlayerStateError(
                        operation="play",
                        current_state=self._state,
                        allowed_states=(
                            PlayerState.IDLE,
                            PlayerState.PAUSED,
                            PlayerState.STOPPED
                        )
                    )

            if self._current is None:
                entry: QueueEntry = self._queue.pop()
            else:
                entry = self._current

                try:
                    await self._start_entry(
                        entry,
                        start_position=entry.start_position,
                        events=events
                    )
                except Exception:
                    self._current = None
                    self._current_source = None
                    self._started_at = None
                    self._position_offset = 0.0
                    self._prepend(entry)
                    self._change_state(PlayerState.STOPPED, events)
                    raise
        finally:
            await self._dispatch_events(events)

    async def pause(self) -> None:
        """Pause active playback.

        Raises:
            InvalidPlayerStateError:
                The player is not actively playing.
            PlayerDestroyedError:
                The player has already been destroyed.
            BackendError:
                The backend could not pause playback.
        """

        self._ensure_active()
        events: list[PlaybackEvent] = []

        async with self._lock:
            if self._state is PlayerState.PLAYING:
                raise InvalidPlayerStateError(
                    operation="pause",
                    current_state=self._state,
                    allowed_states=(PlayerState.PLAYING,)
                )

            await self._backend.pause()
            self._position_offset = self.position
            self._started_at = None
            self._change_state(PlayerState.PAUSED, events)

        await self._dispatch_events(events)

    async def resume(self) -> None:
        """Resume paused playback.

        Raises:
            InvalidPlayerStateError:
                The player is not paused.
            PlayerDestroyedError:
                The player has already been destroyed.
            BackendError:
                The backend could not resume playback.
        """

        self._ensure_active()
        events: list[PlaybackEvent] = []

        async with self._lock:
            if self._state is PlayerState.PAUSED:
                raise InvalidPlayerStateError(
                    operation="resume",
                    current_state=self._state,
                    allowed_states=(PlayerState.PAUSED,)
                )

            await self._backend.resume()
            self._started_at = monotonic()
            self._change_state(PlayerState.PLAYING, events)

        await self._dispatch_events(events)

    async def stop(self, *, clear_queue: bool = False) -> None:
        """Stop active playback.

        Args:
            clear_queue:
                Whether every queued entry should also be removed.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            BackendError:
                The backend could not stop playback.
        """

        self._ensure_active()
        events: list[PlaybackEvent] = []

        async with self._lock:
            if self._current is not None:
                await self._terminate_current(
                    reason=TrackEndReason.STOPPED,
                    events=events
                )
            else:
                self._change_state(PlayerState.STOPPED, events)

            if clear_queue:
                self._queue.clear()

        await self._dispatch_events(events)

    async def skip(self) -> None:
        """Skip the current track and start the next queued entry.

        Raises:
            NoCurrentTrackError:
                No track is currently selected.
            PlayerDestroyedError:
                The player has already been destroyed.
            ResolverError:
                The next track could not be resolved.
            BackendError:
                Playback could not be stopped or restarted.
        """

        self._ensure_active()
        events: list[PlaybackEvent] = []

        try:
            async with self._lock:
                previous_entry: QueueEntry = await self._terminate_current(
                    reason=TrackEndReason.SKIPPED,
                    events=events,
                )
                await self._start_next(
                    previous_entry=previous_entry,
                    events=events
                )
        finally:
            await self._dispatch_events(events)

    async def previous(self) -> None:
        """Return to the most recently played track.

        The currently active entry is inserted at the beginning of the queue so
        it can be played again after the selected history entry.

        Raises:
            QueueEmptyError:
                Playback history contains no entry.
            PlayerDestroyedError:
                The player has already been destroyed.
            ResolverError:
                The previous track could not be resolved.
            BackendError:
                Playback could not be stopped or restarted.
        """

        self._ensure_active()
        events: list[PlaybackEvent] = []

        try:
            async with self._lock:
                if not self._history:
                    raise QueueEmptyError

                previous_entry: QueueEntry = self._history.pop()
                replaced_entry: QueueEntry | None = None

                if self._current is not None:
                    replaced_entry = await self._terminate_current(
                        reason=TrackEndReason.REPLACED,
                        events=events,
                        add_to_history=False
                    )
                    self._prepend(replaced_entry)

                try:
                    await self._start_entry(
                        previous_entry,
                        start_position=previous_entry.start_position,
                        events=events
                    )
                except Exception:
                    self._history.append(previous_entry)

                    if replaced_entry is not None:
                        self._queue.remove_entry(replaced_entry.identifier)

                    raise
        finally:
            await self._dispatch_events(events)

    async def seek(self, position: float) -> None:
        """Restart the current track from another position.

        Args:
            position:
                The desired playback position in seconds.

        Raises:
            NoCurrentTrackError:
                No track is currently selected.
            InvalidPlayerStateError:
                The active source does not support seeking.
            PlayerDestroyedError:
                The player has already been destroyed.
            ValueError:
                The position is invalid or exceeds the track duration.
            ResolverError:
                A replacement source could not be resolved.
            BackendError:
                Playback could not be restarted.
        """

        self._ensure_active()
        normalized_position: float = self._validate_position(position)
        events: list[PlaybackEvent] = []

        try:
            async with self._lock:
                entry: QueueEntry | None = self._current
                source: PlayableSource | None = self._current_source

                if entry is None:
                    raise NoCurrentTrackError

                if source is not None and not source.seekable:
                    raise InvalidPlayerStateError(
                        operation="seek",
                        current_state=self._state,
                        allowed_states=()
                    )

                duration: float | None = entry.track.duration

                if (
                    duration is not None
                    and normalized_position > duration
                ):
                    raise ValueError(
                        "The playback position cannot exceed the track "
                        "duration."
                    )

                self._playback_generation += 1

                if (
                    self._backend.connected
                    and (
                        self._backend.playing
                        or self._backend.paused
                    )
                ):
                    await self._backend.stop()

                self._current = None
                self._current_source = None
                self._started_at = None
                self._position_offset = 0.0

                await self._start_entry(
                    entry,
                    start_position=normalized_position,
                    events=events
                )
        finally:
            await self._dispatch_events(events)

    def shuffle(self) -> None:
        """Randomize queued playback entries.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
        """

        self._ensure_active()
        self._queue.shuffle()

    def set_loop(self, loop_mode: LoopMode) -> None:
        """Change the active playback loop mode.

        Args:
            loop_mode:
                The loop behavior applied after track completion.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            TypeError:
                The supplied value is not a loop mode.
        """

        self._ensure_active()

        if not isinstance(loop_mode, LoopMode):
            raise TypeError("The player loop mode must be a LoopMode value.")

        self._loop_mode = loop_mode

    async def set_volume(self, volume: float) -> None:
        """Change the current playback volume.

        Args:
            volume:
                The new non-negative playback volume.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            ValueError:
                The volume is invalid.
            BackendError:
                The backend rejected the volume change.
        """

        self._ensure_active()
        normalized_volume: float = self._validate_volume(volume)

        async with self._lock:
            await self._backend.set_volume(normalized_volume)
            self._volume = normalized_volume

    def remove(self, index: int) -> QueueEntry:
        """Remove one queued entry by index.

        Args:
            index:
                The queue index to remove.

        Returns:
            The removed queue entry.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            QueueIndexOutOfRangeError:
                The index is outside the queue.
        """

        self._ensure_active()
        return self._queue.pop(index)

    def move(self, current_index: int, target_index: int) -> None:
        """Move a queued entry to another index.

        Args:
            current_index:
                The current queue index of the entry.
            target_index:
                The desired final queue index.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            QueueIndexOutOfRangeError:
                Either index is outside the queue.
        """

        self._ensure_active()
        self._queue.move(current_index, target_index)

    def clear(self) -> tuple[QueueEntry, ...]:
        """Remove every queued entry.

        Returns:
            The removed entries in their previous playback order.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
        """

        self._ensure_active()
        return self._queue.clear()

    async def disconnect(self) -> None:
        """Stop playback and disconnect the playback backend.

        Raises:
            PlayerDestroyedError:
                The player has already been destroyed.
            BackendError:
                Playback or disconnection failed.
        """

        self._ensure_active()
        await self.stop()
        await self._backend.disconnect()

    async def destroy(self) -> None:
        """Release every resource owned by the media player.

        Calling this method more than once has no effect. Cleanup failures are
        grouped so every owned dependency receives a close request.

        Raises:
            ExceptionGroup:
                One or more player dependencies failed during cleanup.
        """

        if self._destroyed:
            return

        events: list[PlaybackEvent] = []
        exceptions: list[Exception] = []

        async with self._lock:
            if self._current is not None:
                try:
                    await self._terminate_current(
                        reason=TrackEndReason.STOPPED,
                        events=events
                    )
                except Exception as exception:
                    exceptions.append(exception)

            self._queue.clear()
            self._history.clear()
            self._destroyed = True
            self._change_state(PlayerState.DESTROYED, events)
            events.append(PlayerDestroyEvent())

        try:
            await self._backend.close()
        except Exception as exception:
            exceptions.append(exception)

        if self._close_resolvers:
            try:
                await self._resolvers.close()
            except Exception as exception:
                exceptions.append(exception)

        await self._dispatch_events(events)

        if exceptions:
            raise ExceptionGroup(
                "One or more media player resources failed to close.",
                exceptions
            )

    async def _start_entry(
            self,
            entry: QueueEntry,
            *,
            start_position: float,
            events: list[PlaybackEvent]
    ) -> None:
        """Resolve and begin playing one queue entry.

        Args:
            entry:
                The queue entry to begin playing.
            start_position:
                The initial playback position in seconds.
            events:
                The event collection receiving generated playback events.

        Raises:
            ResolverError:
                The media track could not be resolved.
            BackendError:
                The backend could not connect or begin playback.
        """

        normalized_position: float = self._validate_position(start_position)

        if not self._backend.connected:
            await self._backend.connect()

        self._change_state(PlayerState.BUFFERING, events)
        source: PlayableSource = await self._resolvers.resolve(entry.track)

        self._playback_generation += 1
        playback_generation: int = self._playback_generation

        async def on_complete(error: Exception | None) -> None:
            """Process backend playback completion."""

            await self._handle_backend_completion(
                playback_generation,
                error,
            )

        await self._backend.play(
            source,
            start_position=normalized_position,
            volume=self._volume,
            on_complete=on_complete
        )

        self._current = entry
        self._current_source = source
        self._position_offset = normalized_position
        self._started_at = monotonic()
        self._change_state(PlayerState.PLAYING, events)
        events.append(TrackStartEvent(entry=entry))

    async def _terminate_current(
            self,
            *,
            reason: TrackEndReason,
            events: list[PlaybackEvent],
            add_to_history: bool = True
    ) -> QueueEntry:
        """Stop and finalize the current queue entry.

        Args:
            reason:
                The reason why the current track is ending.
            events:
                The event collection receiving generated playback events.
            add_to_history:
                Whether the current entry should be added to playback history.

        Returns:
            The queue entry that was stopped.

        Raises:
            NoCurrentTrackError:
                No track is currently selected.
            BackendError:
                The backend could not stop playback.
        """

        entry: QueueEntry | None = self._current

        if entry is None:
            raise NoCurrentTrackError

        self._playback_generation += 1

        if (
                self._backend.connected
                and (
                self._backend.playing
                or self._backend.paused
        )
        ):
            await self._backend.stop()

        self._current = None
        self._current_source = None
        self._started_at = None
        self._position_offset = 0.0

        if add_to_history:
            self._append_history(entry)

        events.append(
            TrackEndEvent(
                entry=entry,
                reason=reason
            )
        )
        self._change_state(PlayerState.STOPPED, events)

        return entry

    async def _start_next(self, *, previous_entry: QueueEntry | None, events: list[PlaybackEvent]) -> None:
        """Start the next queued entry.

        Args:
            previous_entry:
                The entry that played before the queue became empty.
            events:
                The event collection receiving generated playback events.

        Raises:
            ResolverError:
                The next media track could not be resolved.
            BackendError:
                The backend could not begin playback.
        """

        if self._queue.is_empty:
            self._change_state(PlayerState.IDLE, events)
            events.append(QueueEmptyEvent(revious_entry=previous_entry))
            return

        next_entry: QueueEntry = self._queue.pop()

        try:
            await self._start_entry(
                next_entry,
                start_position=next_entry.start_position,
                events=events
            )
        except Exception:
            self._prepend(next_entry)
            self._change_state(PlayerState.STOPPED, events)
            raise

    async def _handle_backend_completion(self, playback_generation: int, error: Exception | None) -> None:
        """Process natural backend playback completion.

        Args:
            playback_generation:
                The generation identifying the completed playback operation.
            error:
                The backend playback exception, when present.
        """

        events: list[PlaybackEvent] = []

        async with self._lock:
            if (
                    playback_generation != self._playback_generation
                    or self._current is None
                    or self._destroyed
            ):
                return

            entry: QueueEntry = self._current
            end_reason: TrackEndReason = (
                TrackEndReason.ERROR
                if error is not None
                else TrackEndReason.FINISHED
            )

            self._current = None
            self._current_source = None
            self._started_at = None
            self._position_offset = 0.0

            events.append(
                TrackEndEvent(
                    entry=entry,
                    reason=end_reason,
                    exception=error
                )
            )

            if (
                    end_reason is TrackEndReason.FINISHED
                    and self._loop_mode is LoopMode.TRACK
            ):
                try:
                    await self._start_entry(
                        entry,
                        start_position=entry.start_position,
                        events=events
                    )
                except Exception:
                    self._append_history(entry)
                    self._change_state(PlayerState.STOPPED, events)
                    _logger.exception("The player could not repeat the current track.")
            else:
                self._append_history(entry)

                if (
                        end_reason is TrackEndReason.FINISHED
                        and self._loop_mode is LoopMode.QUEUE
                ):
                    self._queue.add_entry(entry)

                try:
                    await self._start_next(
                        previous_entry=entry,
                        events=events
                    )
                except Exception:
                    self._change_state(PlayerState.STOPPED, events)
                    _logger.exception("The player could not start the next queued track.")

        await self._dispatch_events(events)

    def _change_state(self, state: PlayerState, events: list[PlaybackEvent]) -> None:
        """Change the player state and append a state event.

        Args:
            state:
                The new player state.
            events:
                The event collection receiving the state-change event.
        """

        if self._state is state:
            return

        previous_state: PlayerState = self._state
        self._state = state
        events.append(
            PlayerStateChangeEvent(
                previous_state=previous_state,
                current_state=state
            )
        )

    async def _dispatch_events(self, events: Iterable[PlaybackEvent]) -> None:
        """Dispatch playback events in their original order.

        Args:
            events:
                The playback events to dispatch.
        """

        for event in events:
            await self._dispatcher.dispatch(event)

    def _prepend(self, entry: QueueEntry) -> None:
        """Insert an entry at the beginning of the playback queue.

        Args:
            entry:
                The queue entry to insert.
        """

        self._queue = PlaybackQueue(
            (
                entry,
                *self._queue.entries,
            )
        )

    def _append_history(self, entry: QueueEntry) -> None:
        """Add an entry to playback history.

        Args:
            entry:
                The completed queue entry to retain.
        """

        if self._history_limit == 0:
            return

        self._history.append(entry)

        if len(self._history) > self._history_limit:
            del self._history[: len(self._history) - self._history_limit]

    @staticmethod
    def _validate_position(position: float) -> float:
        """Validate a playback position.

        Args:
            position:
                The playback position in seconds.

        Returns:
            The validated position as a float.

        Raises:
            ValueError:
                The position is negative or not finite.
        """

        if not isfinite(position) or position < 0.0:
            raise ValueError("The playback position must be finite and non-negative.")

        return float(position)

    @staticmethod
    def _validate_volume(volume: float) -> float:
        """Validate a playback volume.

        Args:
            volume:
                The playback volume to validate.

        Returns:
            The validated volume as a float.

        Raises:
            ValueError:
                The volume is negative or not finite.
        """

        if not isfinite(volume) or volume < 0.0:
            raise ValueError("The playback volume must be finite and non-negative.")

        return float(volume)

    def _ensure_active(self) -> None:
        """Ensure that the player has not been destroyed.

        Raises:
            PlayerDestroyedError:
                The player has already released its resources.
        """

        if self._destroyed:
            raise PlayerDestroyedError

    @staticmethod
    def _consume_completion_task(task: Task[None]) -> None:
        """Consume and log asynchronous completion failures.

        Args:
            task:
                The completed backend callback task.
        """

        try:
            task.result()
        except CancelledError:
            return
        except Exception:
            _logger.exception("A media player completion callback failed.")

__all__: tuple[str, ...] = ("WumpiWavePlayer",)

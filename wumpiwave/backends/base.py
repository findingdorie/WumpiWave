"""Base playback backend implementation used throughout WumpiWave.

This module provides shared backend identification, lifecycle management,
state validation, and playback parameter validation for concrete playback
backend implementations.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import isfinite

from ..exceptions import BackendError
from ..models import PlayableSource
from ..playback import PlaybackQueue
from ..protocols import PlaybackCompletionCallback

class BasePlaybackBackend(ABC):
    """Provide shared functionality for playback backend implementations.

    Playback backends may inherit from this class to receive normalized backend
    names, idempotent resource cleanup, closed-state validation, playback
    position validation, and volume validation.

    Concrete implementations remain responsible for managing their connection,
    active audio source, playback state, and external playback system.

    Attributes:
        name:
            The normalized public name used to identify the backend.
        closed:
            Whether the backend has released its resources.
        connected:
            Whether the backend is connected to its playback destination.
        playing:
            Whether the backend is currently playing an audio source.
        paused:
            Whether playback is currently paused.
        volume:
            The current normalized playback volume.

    Methods:
        connect:
            Connect the backend to its configured playback destination.
        disconnect:
            Disconnect the backend from its playback destination.
        play:
            Begin playing a resolved media source.
        pause:
            Pause the active playback operation.
        resume:
            Resume the paused playback operation.
        stop:
            Stop the active playback operation.
        set_volume:
            Change the current playback volume.
        close:
            Release all resources owned by the backend.
        _close:
            Perform backend-specific resource cleanup.
        _ensure_open:
            Ensure that the backend has not been closed.
        _validate_start_position:
            Validate and normalize a playback start position.
        _validate_volume:
            Validate and normalize a playback volume.
    """

    __slots__ = (
        "_closed",
        "_name"
    )

    _closed: bool
    _name: str

    def __init__(self, name: str) -> None:
        """Initialize a playback backend.

        Args:
            name:
                The public name used to identify the backend.

        Raises:
            ValueError:
                The supplied backend name is empty.
        """

        normalized_name: str = name.strip()

        if not normalized_name:
            raise ValueError("The playback backend name cannot be empty.")

        self._name = normalized_name
        self._closed = False

    @property
    def name(self) -> str:
        """Return the public backend name.

        Returns:
            The normalized name used to identify the playback backend.
        """

        return self._name

    @property
    def closed(self) -> bool:
        """Return whether the backend has been closed.

        Returns:
            ``True`` when backend resources have been released.
        """

        return self._closed

    @property
    @abstractmethod
    def connected(self) -> bool:
        """Return whether the backend is connected.

        Returns:
            ``True`` when the playback destination is connected.
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def playing(self) -> bool:
        """Return whether the backend is actively playing audio.

        Returns:
            ``True`` when an audio source is currently playing.
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def paused(self) -> bool:
        """Return whether playback is currently paused.

        Returns:
            ``True`` when the active playback operation is paused.
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def volume(self) -> float:
        """Return the current playback volume.

        Returns:
            The normalized non-negative playback volume.
        """

        raise NotImplementedError

    @abstractmethod
    async def connect(self) -> None:
        """Connect the backend to its playback destination.

        Raises:
            BackendConnectionError:
                The backend could not establish its connection.
            BackendError:
                The backend has already been closed.
        """

        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect the backend from its playback destination.

        Disconnecting an already disconnected backend should have no effect.

        Raises:
            BackendConnectionError:
                The backend could not close its connection cleanly.
        """

        raise NotImplementedError

    @abstractmethod
    async def play(
        self,
        source: PlayableSource,
        *,
        start_position: float = 0.0,
        volume: float = 1.0,
        on_complete: PlaybackCompletionCallback | None = None,
    ) -> None:
        """Begin playing a resolved media source.

        Args:
            source:
                The resolved media source to play.
            start_position:
                The initial playback position in seconds.
            volume:
                The non-negative playback volume.
            on_complete:
                The optional callback invoked when playback finishes.

        Raises:
            BackendNotConnectedError:
                The backend is not connected to a playback destination.
            BackendPlaybackError:
                Playback could not be started.
            BackendError:
                The backend has already been closed.
            ValueError:
                The start position or volume is invalid.
        """

        raise NotImplementedError

    @abstractmethod
    async def pause(self) -> None:
        """Pause the active playback operation.

        Raises:
            BackendNotConnectedError:
                The backend is not connected.
            BackendPlaybackError:
                No active playback operation can be paused.
            BackendError:
                The backend has already been closed.
        """

        raise NotImplementedError

    @abstractmethod
    async def resume(self) -> None:
        """Resume the paused playback operation.

        Raises:
            BackendNotConnectedError:
                The backend is not connected.
            BackendPlaybackError:
                No paused playback operation can be resumed.
            BackendError:
                The backend has already been closed.
        """

        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Stop the active playback operation.

        Stopping an idle backend should have no effect.

        Raises:
            BackendNotConnectedError:
                The backend is not connected.
            BackendPlaybackError:
                The active playback operation could not be stopped.
            BackendError:
                The backend has already been closed.
        """

        raise NotImplementedError

    @abstractmethod
    async def set_volume(self, volume: float) -> None:
        """Change the current playback volume.

        Args:
            volume:
                The new non-negative playback volume.

        Raises:
            BackendPlaybackError:
                The backend cannot change the current playback volume.
            BackendError:
                The backend has already been closed.
            ValueError:
                The supplied volume is invalid.
        """

        raise NotImplementedError

    async def close(self) -> None:
        """Release all resources owned by the playback backend.

        Calling this method more than once has no effect.
        """

        if self._closed:
            return

        self._closed = True
        await self._close()

    @abstractmethod
    async def _close(self) -> None:
        """Perform backend-specific resource cleanup.

        Implementations should stop active playback, disconnect from external
        playback destinations, and release every resource owned by the backend.
        """

        raise NotImplementedError

    def _ensure_open(self) -> None:
        """Ensure that the playback backend has not been closed.

        Raises:
            BackendError:
                The backend has already released its resources.
        """

        if self._closed:
            raise BackendError(
                message="The playback backend has already been closed.",
                backend_name=self._name
            )

    @staticmethod
    def _validate_start_position(start_position: float) -> float:
        """Validate and normalize a playback start position.

        Args:
            start_position:
                The initial playback position in seconds.

        Returns:
            The validated playback position.

        Raises:
            ValueError:
                The position is negative or not finite.
        """

        if not isfinite(start_position) or start_position < 0.0:
            raise ValueError(
                "The playback start position must be finite and "
                "non-negative."
            )

        return float(start_position)

    @staticmethod
    def _validate_volume(volume: float) -> float:
        """Validate and normalize a playback volume.

        Args:
            volume:
                The playback volume to validate.

        Returns:
            The validated non-negative playback volume.

        Raises:
            ValueError:
                The volume is negative or not finite.
        """

        if not isfinite(volume) or volume < 0.0:
            raise ValueError(
                "The playback volume must be finite and non-negative."
            )

        return float(volume)

__all__: tuple[str, ...] = ("BasePlaybackBackend",)
"""Base stream resolver implementation used throughout WumpiWave.

This module provides shared resolver identification, lifecycle management,
resource cleanup, and closed-state validation for stream resolvers.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..exceptions import ResolverError
from ..models import MediaTrack, PlayableSource

class BaseStreamResolver(ABC):
    """Provide shared functionality for stream resolver implementations.

    Stream resolvers may inherit from this class to receive normalized resolver
    names, idempotent resource cleanup, and closed-state validation.

    Attributes:
        name:
            The normalized public name used to identify the resolver.
        closed:
            Whether the resolver has released its resources.

    Methods:
        supports:
            Determine whether the resolver can process a media track.
        resolve:
            Convert a media track into a playable audio source.
        close:
            Release resources owned by the resolver.
        _close:
            Perform resolver-specific resource cleanup.
        _ensure_open:
            Ensure that the resolver has not been closed.
    """

    __slots__ = (
        "_closed",
        "_name"
    )

    _closed: bool
    _name: str

    def __init__(self, name: str) -> None:
        """Initialize a stream resolver.

        Args:
            name:
                The public name used to identify the resolver.

        Raises:
            ValueError:
                The supplied resolver name is empty.
        """

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("The resolver name cannot be empty.")

        self._name = normalized_name
        self._closed = False

    @property
    def name(self) -> str:
        """Return the public resolver name.

        Returns:
            The normalized name used for registration and lookup.
        """

        return self._name

    @property
    def closed(self) -> bool:
        """Return whether the resolver has been closed.

        Returns:
            ``True`` when resolver resources have been released, otherwise
            ``False``.
        """

        return self._closed

    @abstractmethod
    def supports(self, track: MediaTrack) -> bool:
        """Return whether the resolver supports a media track.

        Args:
            track:
                The normalized media track to inspect.

        Returns:
            ``True`` when the resolver can process the track, otherwise
            ``False``.
        """

        raise NotImplementedError

    @abstractmethod
    async def resolve(self, track: MediaTrack) -> PlayableSource:
        """Resolve a media track into a playable audio source.

        Args:
            track:
                The normalized media track to resolve.

        Returns:
            A temporary playable source containing the resolved stream and
            required connection metadata.

        Raises:
            ResolverError:
                The resolver could not produce a playable source.
            StreamNotFoundError:
                No playable stream could be located for the track.
        """

        raise NotImplementedError

    async def close(self) -> None:
        """Release resources owned by the resolver.

        Calling this method more than once has no effect.
        """

        if self._closed:
            return

        self._closed = True
        await self._close()

    @abstractmethod
    async def _close(self) -> None:
        """Perform resolver-specific resource cleanup.

        Implementations should close network sessions, extraction clients, and
        other resources owned by the resolver.
        """

        raise NotImplementedError

    def _ensure_open(self) -> None:
        """Ensure that the resolver has not been closed.

        Raises:
            ResolverError:
                The resolver has already released its resources.
        """

        if self._closed:
            raise ResolverError(
                message="The stream resolver has already been closed.",
                resolver_name=self._name,
            )

__all__: tuple[str, ...] = ("BaseStreamResolver",)
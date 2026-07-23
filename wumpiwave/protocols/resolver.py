"""Stream resolver protocol used throughout WumpiWave.

This module defines the structural interface required for stream resolvers
that convert normalized media tracks into playable audio sources.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import MediaTrack, PlayableSource


@runtime_checkable
class StreamResolver(Protocol):
    """Define the interface required for stream resolvers.

    A stream resolver converts normalized track metadata into a temporary
    playable source. Implementations do not need to inherit from this protocol
    as long as they provide the required attributes and methods.

    Attributes:
        name:
            The unique public name used to register and identify the resolver.

    Methods:
        supports:
            Determine whether the resolver can process a media track.
        resolve:
            Convert a media track into a playable audio source.
        close:
            Release network sessions and other resources owned by the resolver.
    """

    @property
    def name(self) -> str:
        """Return the unique public name of the resolver.

        Returns:
            The resolver name used during registration and lookup.
        """

        ...

    def supports(self, track: MediaTrack) -> bool:
        """Return whether the resolver supports a media track.

        This method should only inspect the normalized track and must not
        perform network requests.

        Args:
            track:
                The normalized media track to inspect.

        Returns:
            ``True`` when the resolver can process the track, otherwise
            ``False``.
        """

        ...

    async def resolve(self, track: MediaTrack) -> PlayableSource:
        """Resolve a media track into a playable audio source.

        Args:
            track:
                The normalized media track to resolve.

        Returns:
            A temporary playable source containing the resolved stream URL and
            required connection metadata.

        Raises:
            ResolverError:
                The resolver could not produce a playable source.
            StreamNotFoundError:
                No playable stream could be located for the track.
        """

        ...

    async def close(self) -> None:
        """Release resources owned by the resolver.

        Calling this method more than once should not raise an exception.
        """

        ...


__all__: tuple[str, ...] = ("StreamResolver",)
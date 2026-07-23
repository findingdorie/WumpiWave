"""Metadata provider protocol used throughout WumpiWave.

This module defines the structural interface required for metadata providers
that retrieve tracks, playlists, albums, and other media information.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import MediaQuery, MediaResult, MediaSource

@runtime_checkable
class MediaProvider(Protocol):
    """Define the interface required for metadata providers.

    A media provider retrieves normalized media metadata from an external
    service such as YouTube or Spotify. Implementations do not need to inherit
    from this protocol as long as they provide the required attributes and
    methods.

    Attributes:
        name:
            The unique public name used to register and identify the provider.
        source:
            The media source handled by the provider.

    Methods:
        supports:
            Determine whether the provider can process a media query.
        query:
            Process a media query and return normalized media metadata.
        close:
            Release network sessions and other resources owned by the provider.
    """

    @property
    def name(self) -> str:
        """Return the unique public name of the provider.

        Returns:
            The provider name used during registration and lookup.
        """

        ...

    @property
    def source(self) -> MediaSource:
        """Return the media source handled by the provider.

        Returns:
            The source associated with media returned by the provider.
        """

        ...

    def supports(self, query: MediaQuery) -> bool:
        """Return whether the provider supports a media query.

        This method should only inspect the normalized query and must not
        perform network requests.

        Args:
            query:
                The normalized media query to inspect.

        Returns:
            ``True`` when the provider can process the query, otherwise
            ``False``.
        """

        ...

    async def query(self, query: MediaQuery) -> MediaResult:
        """Process a media query and retrieve normalized metadata.

        Args:
            query:
                The normalized media query to process.

        Returns:
            The normalized media result returned by the provider.

        Raises:
            ProviderError:
                The provider could not complete the query.
            QueryError:
                The supplied query is invalid or produced no media.
        """

        ...

    async def close(self) -> None:
        """Release resources owned by the provider.

        Calling this method more than once should not raise an exception.
        """

        ...

__all__: tuple[str, ...] = ("MediaProvider",)
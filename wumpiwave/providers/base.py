"""Base metadata provider implementation used throughout WumpiWave.

This module provides shared provider identification, lifecycle management,
resource cleanup, and closed-state validation for metadata providers.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..exceptions import ProviderUnavailableError
from ..models import MediaQuery, MediaResult, MediaSource


class BaseMediaProvider(ABC):
    """Provide shared functionality for metadata provider implementations.

    Metadata providers may inherit from this class to receive normalized
    provider names, source information, idempotent resource cleanup, and
    closed-state validation.

    Attributes:
        name:
            The normalized public name used to identify the provider.
        source:
            The media source handled by the provider.
        closed:
            Whether the provider has released its resources.

    Methods:
        supports:
            Determine whether the provider can process a media query.
        query:
            Process a media query and return normalized metadata.
        close:
            Release resources owned by the provider.
        _close:
            Perform provider-specific resource cleanup.
        _ensure_open:
            Ensure that the provider has not been closed.
    """

    __slots__ = (
        "_closed",
        "_name",
        "_source"
    )

    _closed: bool
    _name: str
    _source: MediaSource

    def __init__(self, name: str, source: MediaSource) -> None:
        """Initialize a metadata provider.

        Args:
            name:
                The public name used to identify the provider.
            source:
                The media source handled by the provider.

        Raises:
            ValueError:
                The supplied provider name is empty.
        """

        normalized_name: str = name.strip()

        if not normalized_name:
            raise ValueError("The provider name cannot be empty.")

        self._name = normalized_name
        self._source = source
        self._closed = False

    @property
    def name(self) -> str:
        """Return the public provider name.

        Returns:
            The normalized name used for provider registration and lookup.
        """

        return self._name

    @property
    def source(self) -> MediaSource:
        """Return the media source handled by the provider.

        Returns:
            The source associated with metadata returned by the provider.
        """

        return self._source

    @property
    def closed(self) -> bool:
        """Return whether the provider has been closed.

        Returns:
            ``True`` when provider resources have been released, otherwise
            ``False``.
        """

        return self._closed

    @abstractmethod
    def supports(self, query: MediaQuery) -> bool:
        """Return whether the provider supports a media query.

        Args:
            query:
                The normalized media query to inspect.

        Returns:
            ``True`` when the provider can process the query, otherwise
            ``False``.
        """

        raise NotImplementedError

    @abstractmethod
    async def query(self, query: MediaQuery) -> MediaResult:
        """Process a media query and retrieve normalized metadata.

        Args:
            query:
                The normalized media query to process.

        Returns:
            The normalized media result produced by the provider.

        Raises:
            ProviderError:
                The provider could not complete the request.
            QueryError:
                The supplied query is invalid or produced no matching media.
        """

        raise NotImplementedError

    async def close(self) -> None:
        """Release resources owned by the provider.

        Calling this method more than once has no effect.
        """

        if self._closed:
            return

        self._closed = True
        await self._close()

    @abstractmethod
    async def _close(self) -> None:
        """Perform provider-specific resource cleanup.

        Implementations should close network sessions, clients, and other
        resources owned by the provider.
        """

        raise NotImplementedError

    def _ensure_open(self) -> None:
        """Ensure that the provider has not been closed.

        Raises:
            ProviderUnavailableError:
                The provider has already released its resources.
        """

        if self._closed:
            raise ProviderUnavailableError(
                provider_name=self._name,
                reason="The provider has already been closed."
            )

__all__: tuple[str, ...] = ("BaseMediaProvider",)
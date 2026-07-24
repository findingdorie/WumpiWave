"""Stream resolver registry used by WumpiWave.

This module manages resolver registration, lookup, selection, stream
resolution, lifecycle handling, and resource cleanup.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from types import TracebackType
from typing import Self

from ..exceptions import (
    ResolverAlreadyRegisteredError,
    ResolverError,
    ResolverNotFoundError,
    UnsupportedMediaError,
)
from ..models import MediaTrack, PlayableSource
from ..protocols import StreamResolver

class ResolverRegistry:
    """Manage stream resolvers available to a WumpiWave player.

    Resolvers are stored by their case-insensitive public names while
    preserving their registration order. Track resolution uses the first
    registered resolver that reports support for the supplied media track.

    The registry may be used as an asynchronous context manager. Closing it
    closes every registered resolver and prevents further operations.

    Attributes:
        closed:
            Whether the registry and its registered resolvers have been closed.
        names:
            The public names of all registered resolvers.
        resolvers:
            The registered resolvers in their selection order.

    Methods:
        register:
            Add a resolver to the registry.
        register_all:
            Add multiple resolvers to the registry.
        unregister:
            Remove and return a resolver without closing it.
        get:
            Return a resolver by its public name.
        select:
            Select the first resolver supporting a media track.
        supports:
            Determine whether any registered resolver supports a media track.
        resolve:
            Resolve a media track into a playable source.
        close:
            Close all registered resolvers and the registry.
        __contains__:
            Determine whether a resolver name is registered.
        __iter__:
            Iterate over registered resolvers.
        __len__:
            Return the number of registered resolvers.
        __aenter__:
            Enter the asynchronous registry context.
        __aexit__:
            Leave the asynchronous registry context and close the registry.
        _normalize_name:
            Normalize and validate a resolver name.
        _ensure_open:
            Ensure that the registry has not been closed.
    """

    __slots__ = (
        "_closed",
        "_resolvers"
    )

    _closed: bool
    _resolvers: dict[str, StreamResolver]

    def __init__(self, resolvers: Iterable[StreamResolver] = ()) -> None:
        """Initialize a stream resolver registry.

        Args:
            resolvers:
                The resolvers registered during initialization.

        Raises:
            ResolverAlreadyRegisteredError:
                Multiple supplied resolvers use the same normalized name.
        """

        self._closed = False
        self._resolvers = {}
        self._register_all(resolvers)

    @property
    def closed(self) -> bool:
        """Return whether the registry has been closed.

        Returns:
            ``True`` when the registry can no longer be used.
        """

        return self._closed

    @property
    def names(self) -> tuple[str, ...]:
        """Return the names of all registered resolvers.

        Returns:
            Resolver names in their registration and selection order.
        """

        return tuple(resolver.name for resolver in self._resolvers.values())

    @property
    def resolvers(self) -> tuple[StreamResolver, ...]:
        """Return all registered stream resolvers.

        Returns:
            The resolvers in their registration and selection order.
        """

        return tuple(self._resolvers.values())

    def register(self, resolver: StreamResolver) -> Self:
        """Add a stream resolver to the registry.

        Args:
            resolver:
                The stream resolver to register.

        Returns:
            The registry instance for chained registrations.

        Raises:
            ResolverAlreadyRegisteredError:
                A resolver with the same normalized name is already registered.
            ResolverError:
                The registry has already been closed.
            ValueError:
                The resolver name is empty.
        """

        self._ensure_open()

        resolver_name: str = self._normalize_name(resolver.name)

        if resolver_name is self._resolvers:
            raise ResolverAlreadyRegisteredError(resolver_name=resolver.name)

        self._resolvers[resolver_name] = resolver
        return self

    def register_all(self, resolvers: Iterable[StreamResolver]) -> Self:
        """Add multiple stream resolvers to the registry.

        Args:
            resolvers:
                The stream resolvers to register.

        Returns:
            The registry instance for chained configuration.

        Raises:
            ResolverAlreadyRegisteredError:
                A supplied resolver name is already registered.
            ResolverError:
                The registry has already been closed.
            ValueError:
                A supplied resolver name is empty.
        """

        for resolver in resolvers:
            self.register(resolver)

        return self

    def unregister(self, resolver_name: str) -> StreamResolver:
        """Remove and return a registered stream resolver.

        Removing a resolver does not close it. The caller remains responsible
        for releasing resources owned by the removed resolver.

        Args:
            resolver_name:
                The public name of the resolver to remove.

        Returns:
            The removed stream resolver.

        Raises:
            ResolverNotFoundError:
                No resolver is registered under the supplied name.
            ResolverError:
                The registry has already been closed.
            ValueError:
                The supplied resolver name is empty.
        """

        self._ensure_open()

        normalized_name: str = self._normalize_name(resolver_name)

        try:
            return self._resolvers.pop(normalized_name)
        except KeyError as exception:
            raise ResolverNotFoundError(resolver_name=resolver_name) from exception

    def get(self, resolver_name: str) -> StreamResolver:
        """Return a registered stream resolver by name.

        Args:
            resolver_name:
                The case-insensitive public resolver name.

        Returns:
            The matching registered resolver.

        Raises:
            ResolverNotFoundError:
                No resolver is registered under the supplied name.
            ResolverError:
                The registry has already been closed.
            ValueError:
                The supplied resolver name is empty.
        """

        self._ensure_open()

        normalized_name: str = self._normalize_name(resolver_name)

        try:
            return self._resolvers[normalized_name]
        except KeyError as exception:
            raise ResolverNotFoundError(resolver_name=resolver_name) from exception

    def select(self, track: MediaTrack) -> StreamResolver:
        """Select the first resolver supporting a media track.

        Resolver registration order defines selection priority when multiple
        resolvers support the same track.

        Args:
            track:
                The normalized media track to inspect.

        Returns:
            The first compatible registered stream resolver.

        Raises:
            UnsupportedMediaError:
                No registered resolver supports the supplied track.
            ResolverError:
                The registry has already been closed.
        """

        self._ensure_open()

        for resolver in self._resolvers.values():
            if resolver.supports(track):
                return resolver

        raise UnsupportedMediaError(track=track)

    def supports(self, track: MediaTrack) -> bool:
        """Return whether any registered resolver supports a media track.

        Args:
            track:
                The normalized media track to inspect.

        Returns:
            ``True`` when a compatible resolver is available, otherwise
            ``False``.
        """

        if self._closed:
            return False

        return any(
            resolver.supports(track)
            for resolver in self._resolvers.values()
        )

    async def resolve(self, track: MediaTrack) -> PlayableSource:
        """Resolve a media track into a playable source.

        Args:
            track:
                The normalized media track to resolve.

        Returns:
            The playable source returned by the selected stream resolver.

        Raises:
            UnsupportedMediaError:
                No registered resolver supports the supplied track.
            ResolverError:
                The registry is closed or the selected resolver failed.
        """

        return await self.select(track).resolve(track)

    async def close(self) -> None:
        """Close all registered resolvers and the registry.

        Every registered resolver receives a close request even when another
        resolver fails during cleanup. Multiple cleanup errors are combined
        into an exception group.

        Raises:
            ExceptionGroup:
                One or more registered resolvers failed during cleanup.
        """

        if self._closed:
            return

        self._closed = True
        resolvers: tuple[StreamResolver, ...] = tuple(self._resolvers.values())
        self._resolvers.clear()
        exceptions: list[Exception] = []

        for resolver in resolvers:
            try:
                await resolver.close()
            except Exception as exception:
                exceptions.append(exception)

        if exceptions:
            raise ExceptionGroup(
                "One or more stream resolvers failed to close.",
                exceptions
            )

    def __contains__(self, resolver_name: object) -> bool:
        """Return whether a resolver name is registered.

        Args:
            resolver_name:
                The possible resolver name to inspect.

        Returns:
            ``True`` when the normalized resolver name is registered.
        """

        if not isinstance(resolver_name, str):
            return False

        normalized_name: str = resolver_name.strip().casefold()

        if not normalized_name:
            return False

        return normalized_name in self._resolvers

    def __iter__(self) -> Iterator[StreamResolver]:
        """Iterate over registered stream resolvers.

        Returns:
            An iterator following resolver registration order.
        """

        return iter(self._resolvers.values())

    def __len__(self) -> int:
        """Return the number of registered stream resolvers.

        Returns:
            The current number of registered resolvers.
        """

        return len(self._resolvers)

    async def __aenter__(self) -> Self:
        """Enter the asynchronous registry context.

        Returns:
            The active resolver registry.

        Raises:
            ResolverError:
                The registry has already been closed.
        """

        self._ensure_open()
        return self

    async def __aexit__(
            self,
            exception_type: type[BaseException] | None,
            exception: BaseException | None,
            traceback: TracebackType | None
    ) -> None:
        """Leave the asynchronous registry context.

        Args:
            exception_type:
                The type of exception raised inside the context, when present.
            exception:
                The exception raised inside the context, when present.
            traceback:
                The traceback associated with the exception, when present.
        """

        await self.close()

    @staticmethod
    def _normalize_name(resolver_name: str) -> str:
        """Normalize and validate a resolver name.

        Args:
            resolver_name:
                The resolver name to normalize.

        Returns:
            The normalized case-insensitive resolver name.

        Raises:
            ValueError:
                The supplied resolver name is empty.
        """

        normalized_name: str = resolver_name.strip().casefold()

        if not normalized_name:
            raise ValueError("The resolver name cannot be empty.")

        return normalized_name

    def _ensure_open(self) -> None:
        """Ensure that the registry has not been closed.

        Raises:
            ResolverError:
                The registry has already been closed.
        """

        if self._closed:
            raise ResolverError(message="The stream resolver registry has already been closed.")

__all__: tuple[str, ...] = ("ResolverRegistry",)

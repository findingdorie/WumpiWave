"""Metadata provider registry used by WumpiWave.

This module manages metadata provider registration, lookup, automatic
selection, query routing, and asynchronous resource cleanup.

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
    ProviderAlreadyRegisteredError,
    ProviderError,
    ProviderNotFoundError,
    UnsupportedQueryError
)
from ..models import MediaQuery, MediaResult
from ..protocols import MediaProvider

class ProviderRegistry:
    """Manage metadata providers available to WumpiWave.

    Providers are stored by their case-insensitive public names while
    preserving registration order. Query routing selects the first registered
    provider that reports support for the supplied media query.

    The registry may be used as an asynchronous context manager. Closing the
    registry closes every registered provider and prevents further operations.

    Attributes:
        closed:
            Whether the registry has released its providers.
        names:
            The public names of all registered providers.
        providers:
            The registered providers in their selection order.

    Methods:
        register:
            Add one metadata provider to the registry.
        register_all:
            Add multiple metadata providers atomically.
        unregister:
            Remove and return a provider without closing it.
        get:
            Return a provider by its public name.
        select:
            Select the first provider supporting a media query.
        supports:
            Determine whether any provider supports a media query.
        query:
            Route a media query to a compatible provider.
        close:
            Close all registered providers and the registry.
        __contains__:
            Determine whether a provider name is registered.
        __iter__:
            Iterate over registered metadata providers.
        __len__:
            Return the number of registered providers.
        __bool__:
            Return whether the registry contains any providers.
        __aenter__:
            Enter the asynchronous registry context.
        __aexit__:
            Leave the asynchronous registry context and close the registry.
        _normalize_name:
            Normalize and validate a provider name.
        _ensure_open:
            Ensure that the registry has not been closed.
    """

    __slots__ = (
        "_closed",
        "_providers"
    )

    _closed: bool
    _providers: dict[str, MediaProvider]

    def __init__(self, providers: Iterable[MediaProvider] = ()):
        """Initialize a metadata provider registry.

        Args:
            providers:
                The metadata providers registered during initialization.

        Raises:
            ProviderAlreadyRegisteredError:
                Multiple providers use the same normalized name.
        """

        self._closed = False
        self._providers = {}
        self.register_all(providers)

    @property
    def closed(self) -> bool:
        """Return whether the registry has been closed.

        Returns:
            ``True`` when the registry can no longer be used.
        """

        return self._closed

    @property
    def names(self) -> tuple[str, ...]:
        """Return all registered provider names.

        Returns:
            Provider names in registration and selection order.
        """

        return tuple(provider.name for provider in self._providers.values())

    @property
    def providers(self) -> tuple[MediaProvider, ...]:
        """Return all registered metadata providers.

        Returns:
            Providers in their registration and selection order.
        """

        return tuple(self._providers.values())

    def register(self, provider: MediaProvider) -> Self:
        """Add one metadata provider to the registry.

        Args:
            provider:
                The metadata provider to register.

        Returns:
            The registry instance for chained registrations.

        Raises:
            ProviderAlreadyRegisteredError:
                A provider with the same normalized name is registered.
            ProviderError:
                The registry has already been closed.
            ValueError:
                The provider name is empty.
        """

        self._ensure_open()

        provider_name: str = self._normalize_name(provider.name)

        if provider_name in self._providers:
            raise ProviderAlreadyRegisteredError(provider_name=provider_name)

        self._providers[provider_name] = provider
        return self

    def register_all(self, providers: Iterable[MediaProvider]) -> Self:
        """Add multiple metadata providers atomically.

        Every provider is validated before the registry is modified.

        Args:
            providers:
                The metadata providers to register.

        Returns:
            The registry instance for chained registrations.

        Raises:
            ProviderAlreadyRegisteredError:
                A provider name is registered or occurs multiple times.
            ProviderError:
                The registry has already been closed.
            ValueError:
                A provider name is empty.
        """

        self._ensure_open()

        new_providers: tuple[MediaProvider, ...] = tuple(providers)

        if not new_providers:
            return self

        known_names: set[str] = set(self._providers)
        validated_providers: list[tuple[str, MediaProvider]] = []

        for provider in new_providers:
            provider_name: str = self._normalize_name(provider.name)

            if provider_name in known_names:
                raise ProviderAlreadyRegisteredError(provider_name=provider_name)

            known_names.add(provider_name)
            validated_providers.append(
                (
                    provider_name,
                    provider
                )
            )

        self._providers.update(validated_providers)
        return self

    def unregister(self, provider_name: str) -> MediaProvider:
        """Remove and return a metadata provider.

        Removing a provider does not close it. The caller becomes responsible
        for releasing resources owned by the removed provider.

        Args:
            provider_name:
                The public name of the provider to remove.

        Returns:
            The removed metadata provider.

        Raises:
            ProviderNotFoundError:
                No provider uses the supplied name.
            ProviderError:
                The registry has already been closed.
            ValueError:
                The provider name is empty.
        """

        self._ensure_open()

        normalized_name: str = self._normalize_name(provider_name)

        try:
            return self._providers.pop(normalized_name)
        except KeyError as exception:
            raise ProviderNotFoundError(provider_name=provider_name) from exception

    def get(self, provider_name: str) -> MediaProvider:
        """Return a registered provider by name.

        Args:
            provider_name:
                The case-insensitive public provider name.

        Returns:
            The matching metadata provider.

        Raises:
            ProviderNotFoundError:
                No provider uses the supplied name.
            ProviderError:
                The registry has already been closed.
            ValueError:
                The provider name is empty.
        """

        self._ensure_open()

        normalized_name: str = self._normalize_name(provider_name)

        try:
            return self._providers[normalized_name]
        except KeyError as exception:
            raise ProviderNotFoundError(provider_name=provider_name) from exception

    def select(self, query: MediaQuery) -> MediaProvider:
        """Select the first provider supporting a media query.

        Registration order defines provider priority when multiple providers
        support the same query.

        Args:
            query:
                The normalized media query to inspect.

        Returns:
            The first compatible metadata provider.

        Raises:
            UnsupportedQueryError:
                No provider supports the supplied query.
            ProviderError:
                The registry has already been closed.
        """

        self._ensure_open()

        for provider in self._providers.values():
            if provider.supports(query):
                return provider

        raise UnsupportedQueryError(query_value=query.value)

    def supports(self, query: MediaQuery) -> bool:
        """Return whether any provider supports a media query.

        Args:
            query:
                The normalized media query to inspect.

        Returns:
            ``True`` when a compatible provider is registered.
        """

        if self._closed:
            return False

        return any(
            provider.supports(query)
            for provider in self._providers.values()
        )

    async def query(self, query: MediaQuery) -> MediaResult:
        """Route a media query to a compatible provider.

        Args:
            query:
                The normalized media query to process.

        Returns:
            The media result returned by the selected provider.

        Raises:
            UnsupportedQueryError:
                No provider supports the supplied query.
            ProviderError:
                The registry is closed or the provider request failed.
        """

        return await self.select(query).query(query)

    async def close(self) -> None:
        """Close all registered providers and the registry.

        Every provider receives a close request even when another provider
        fails during cleanup. Providers are closed in reverse registration
        order.

        Raises:
            ExceptionGroup:
                One or more providers failed during cleanup.
        """

        if self._closed:
            return

        self._closed = True
        providers: tuple[MediaProvider, ...] = tuple(reversed(self._providers.values()))
        self._providers.clear()
        exceptions: list[Exception] = []

        for provider in providers:
            try:
                await provider.close()
            except Exception as exception:
                exceptions.append(exception)

        if exceptions:
            raise ExceptionGroup(
                "One or more metadata providers failed to close.",
                exceptions
            )

    def __contains__(self, provider_name: object) -> bool:
        """Return whether a provider name is registered.

        Args:
            provider_name:
                The possible provider name to inspect.

        Returns:
            ``True`` when the normalized provider name is registered.
        """

        if not isinstance(provider_name, str):
            return False

        normalized_name: str = provider_name.strip().casefold()

        if not normalized_name:
            return False

        return normalized_name in self._providers

    def __iter__(self) -> Iterator[MediaProvider]:
        """Iterate over registered metadata providers.

        Returns:
            An iterator following provider registration order.
        """

        return iter(self._providers.values())

    def __len__(self) -> int:
        """Return the number of registered providers.

        Returns:
            The current registry size.
        """

        return len(self._providers)

    def __bool__(self) -> bool:
        """Return whether the registry contains any providers.

        Returns:
            ``True`` when at least one provider is registered.
        """

        return bool(self._providers)

    async def __aenter__(self) -> Self:
        """Enter the asynchronous registry context.

        Returns:
            The active provider registry.

        Raises:
            ProviderError:
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
                The exception type raised inside the context, when present.
            exception:
                The exception raised inside the context, when present.
            traceback:
                The traceback associated with the exception, when present.
        """

        await self.close()

    @staticmethod
    def _normalize_name(provider_name: str) -> str:
        """Normalize and validate a provider name.

        Args:
            provider_name:
                The provider name to normalize.

        Returns:
            The normalized case-insensitive provider name.

        Raises:
            ValueError:
                The supplied provider name is empty.
        """

        normalized_name: str = provider_name.strip().casefold()

        if not normalized_name:
            raise ValueError("The metadata provider name cannot be empty.")

        return normalized_name

    def _ensure_open(self) -> None:
        """Ensure that the registry has not been closed.

        Raises:
            ProviderError:
                The registry has already released its providers.
        """

        if self._closed:
            raise ProviderError(
                provider_name="registry",
                message="The metadata provider registry has already closed."
            )

__all__: tuple[str, ...] = ("ProviderRegistry",)
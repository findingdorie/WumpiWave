"""FFmpeg audio filter chain used by WumpiWave.

This module manages ordered audio filter registration, lookup, activation,
removal, and rendering into one FFmpeg-compatible filter expression.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .base import BaseAudioFilter
from collections.abc import Iterable, Iterator
from typing import Self

class AudioFilterChain:
    """Manage an ordered collection of FFmpeg-compatible audio filters.

    Filters are stored by their case-insensitive public names while preserving
    registration order. Disabled filters remain registered but are omitted
    from the rendered FFmpeg filter expression.

    Attributes:
        names:
            The public names of all registered audio filters.
        filters:
            The registered filters in their rendering order.
        enabled_filters:
            The currently enabled filters in their rendering order.
        is_empty:
            Whether no audio filters are registered.

    Methods:
        add:
            Add one audio filter to the chain.
        extend:
            Add multiple audio filters atomically.
        get:
            Return a registered audio filter by name.
        remove:
            Remove and return a registered audio filter.
        enable:
            Enable a registered audio filter.
        disable:
            Disable a registered audio filter.
        clear:
            Remove and return every registered audio filter.
        render:
            Render enabled filters into one FFmpeg expression.
        __contains__:
            Determine whether a filter or filter name is registered.
        __iter__:
            Iterate over registered audio filters.
        __len__:
            Return the number of registered audio filters.
        __bool__:
            Return whether the chain contains any filters.
        __str__:
            Return the rendered FFmpeg expression.
        _normalize_name:
            Normalize and validate an audio filter name.
        _validate_filter:
            Validate a possible audio filter instance.
    """

    __slots__ = ("_filters",)

    _filters: dict[str, BaseAudioFilter]

    def __init__(self, filters: Iterable[BaseAudioFilter] = ()) -> None:
        """Initialize an audio filter chain.

        Args:
            filters:
                The audio filters registered during initialization.

        Raises:
            TypeError:
                A supplied value is not an audio filter.
            ValueError:
                Multiple filters use the same normalized name.
        """

        self._filters = {}
        self.extend(filters)

    @property
    def names(self) -> tuple[str, ...]:
        """Return the names of all registered audio filters.

        Returns:
            Filter names in their current rendering order.
        """

        return tuple(audio_filter.name for audio_filter in self._filters.values())

    @property
    def filters(self) -> tuple[BaseAudioFilter, ...]:
        """Return all registered audio filters.

        Returns:
            The filters in their current rendering order.
        """

        return tuple(self._filters.values())

    @property
    def enabled_filters(self) -> tuple[BaseAudioFilter, ...]:
        """Return all currently enabled audio filters.

        Returns:
            The enabled filters in their current rendering order.
        """

        return tuple(
            audio_filter
            for audio_filter in self._filters.values()
            if audio_filter.enabled
        )

    @property
    def is_empty(self) -> bool:
        """Return whether no audio filters are registered.

        Returns:
            ``True`` when the chain contains no filters.
        """

        return not self._filters

    def add(self, audio_filter: BaseAudioFilter) -> Self:
        """Add one audio filter to the chain.

        Args:
            audio_filter:
                The audio filter to register.

        Returns:
            The filter chain for chained configuration.

        Raises:
            TypeError:
                The supplied value is not an audio filter.
            ValueError:
                A filter with the same normalized name is already registered.
        """

        self._validate_filter(audio_filter)

        normalized_name: str = self._normalize_name(audio_filter.name)

        if normalized_name in self._filters:
            raise ValueError(f"Audio filter {audio_filter.name!r} is already registered.")

        self._filters[normalized_name] = audio_filter
        return self

    def extend(self, filters: Iterable[BaseAudioFilter]) -> Self:
        """Add multiple audio filters atomically.

        Every filter is validated before the chain is modified. This prevents
        partial registration when one supplied filter is invalid or duplicated.

        Args:
            filters:
                The audio filters to register.

        Returns:
            The filter chain for chained configuration.

        Raises:
            TypeError:
                A supplied value is not an audio filter.
            ValueError:
                A filter name is already registered or occurs multiple times.
        """

        new_filters: tuple[BaseAudioFilter, ...] = tuple(filters)

        if not new_filters:
            return self

        known_names: set[str] = set(self._filters)
        validated_filters: list[tuple[str, BaseAudioFilter]] = []

        for audio_filter in new_filters:
            self._validate_filter(audio_filter)

            normalized_name: str = self._normalize_name(audio_filter.name)

            if normalized_name in known_names:
                raise ValueError(f"Audio filter {audio_filter.name!r} is already registered.")

            known_names.add(normalized_name)
            validated_filters.append(
                (
                    normalized_name,
                    audio_filter
                )
            )

        self._filters.update(validated_filters)
        return self

    def get(self, filter_name: str) -> BaseAudioFilter:
        """Return a registered audio filter by name.

        Args:
            filter_name:
                The case-insensitive public filter name.

        Returns:
            The matching registered audio filter.

        Raises:
            KeyError:
                No audio filter uses the supplied name.
            ValueError:
                The supplied filter name is empty.
        """

        normalized_name: str = self._normalize_name(filter_name)

        try:
            return self._filters[normalized_name]
        except KeyError as exception:
            raise KeyError(f"Audio filter {filter_name!r} is not registered.") from exception

    def remove(self, filter_name: str) -> BaseAudioFilter:
        """Remove and return a registered audio filter.

        Args:
            filter_name:
                The case-insensitive public filter name.

        Returns:
            The removed audio filter.

        Raises:
            KeyError:
                No audio filter uses the supplied name.
            ValueError:
                The supplied filter name is empty.
        """

        normalized_name: str = self._normalize_name(filter_name)

        try:
            return self._filters.pop(normalized_name)
        except KeyError as exception:
            raise KeyError(f"Audio filter {filter_name!r} is not registered.") from exception

    def enable(self, filter_name: str) -> Self:
        """Enable a registered audio filter.

        Args:
            filter_name:
                The case-insensitive public filter name.

        Returns:
            The filter chain for chained configuration.

        Raises:
            KeyError:
                No audio filter uses the supplied name.
            ValueError:
                The supplied filter name is empty.
        """

        self.get(filter_name).enable()
        return self

    def disable(self, filter_name: str) -> Self:
        """Disable a registered audio filter.

        Args:
            filter_name:
                The case-insensitive public filter name.

        Returns:
            The filter chain for chained configuration.

        Raises:
            KeyError:
                No audio filter uses the supplied name.
            ValueError:
                The supplied filter name is empty.
        """

        self.get(filter_name).disable()
        return self

    def clear(self) -> tuple[BaseAudioFilter, ...]:
        """Remove and return every registered audio filter.

        Returns:
            The removed filters in their previous rendering order.
        """

        removed_filters: tuple[BaseAudioFilter, ...] = tuple(self._filters.values())
        self._filters.clear()

        return removed_filters

    def render(self) -> str | None:
        """Render enabled filters into one FFmpeg expression.

        Returns:
            The comma-separated FFmpeg expression, or ``None`` when no enabled
            filters produce an expression.

        Raises:
            ValueError:
                A registered filter produces an invalid expression.
        """

        expressions: tuple[str, ...] = tuple(
            expression
            for audio_filter in self._filters.values()
            if (expression := audio_filter.render()) is not None
        )

        if not expressions:
            return None

        return ",".join(expressions)

    def __contains__(self, value: object) -> bool:
        """Return whether a filter or filter name is registered.

        Args:
            value:
                The possible audio filter or public filter name.

        Returns:
            ``True`` when the associated normalized name is registered.
        """

        if isinstance(value, BaseAudioFilter):
            normalized_name: str = value.name.strip().casefold()
        elif isinstance(value, str):
            normalized_name = value.strip().casefold()
        else:
            return False

        if not normalized_name:
            return False

        return normalized_name in self._filters

    def __iter__(self) -> Iterator[BaseAudioFilter]:
        """Iterate over registered audio filters.

        Returns:
            An iterator following the current rendering order.
        """

        return iter(self._filters.values())

    def __len__(self) -> int:
        """Return the number of registered audio filters.

        Returns:
            The current number of filters in the chain.
        """

        return len(self._filters)

    def __bool__(self) -> bool:
        """Return whether the chain contains any audio filters.

        Returns:
            ``True`` when at least one filter is registered.
        """

        return bool(self._filters)

    def __str__(self) -> str:
        """Return the rendered FFmpeg filter expression.

        Returns:
            The active expression, or an empty string when none is available.
        """

        return self.render() or ""

    @staticmethod
    def _normalize_name(filter_name: str) -> str:
        """Normalize and validate an audio filter name.

        Args:
            filter_name:
                The filter name to normalize.

        Returns:
            The normalized case-insensitive filter name.

        Raises:
            ValueError:
                The supplied filter name is empty.
        """

        normalized_name: str = filter_name.strip().casefold()

        if not normalized_name:
            raise ValueError("The audio filter name cannot be empty.")

        return normalized_name

    @staticmethod
    def _validate_filter(audio_filter: BaseAudioFilter) -> None:
        """Validate a possible audio filter instance.

        Args:
            audio_filter:
                The value to validate.

        Raises:
            TypeError:
                The supplied value is not an audio filter.
        """

        if not isinstance(audio_filter, BaseAudioFilter):
            raise TypeError(
                "The audio filter chain only accepts BaseAudioFilter "
                "instances."
            )

__all__: tuple[str, ...] = ("AudioFilterChain",)
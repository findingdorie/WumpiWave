"""Base audio filter implementation used throughout WumpiWave.

This module provides shared identification, activation control, expression
validation, and rendering for FFmpeg-compatible audio filters.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

class BaseAudioFilter(ABC):
    """Provide shared functionality for FFmpeg-compatible audio filters.

    Concrete filters implement ``build_expression`` to generate their FFmpeg
    audio filter expression. Disabled filters remain configured but are omitted
    when an active filter chain is rendered.

    Attributes:
        name:
            The normalized public name used to identify the filter.
        enabled:
            Whether the filter should be included in an active filter chain.

    Methods:
        build_expression:
            Build the filter-specific FFmpeg expression.
        render:
            Validate and return the active FFmpeg filter expression.
        enable:
            Enable the audio filter.
        disable:
            Disable the audio filter.
        set_enabled:
            Change whether the audio filter is enabled.
        __bool__:
            Return whether the filter is currently enabled.
        __str__:
            Return the rendered expression or an empty string.
        _validate_expression:
            Validate a generated FFmpeg filter expression.
    """

    __slots__ = (
        "_enabled",
        "_name"
    )

    _enabled: bool
    _name: str

    def __init__(self, name: str, *, enabled: bool = True) -> None:
        """Initialize an audio filter.

        Args:
            name:
                The public name used to identify the filter.
            enabled:
                Whether the filter should initially be active.

        Raises:
            TypeError:
                The enabled state is not a boolean.
            ValueError:
                The supplied filter name is empty.
        """

        normalized_name: str = name.strip()

        if not normalized_name:
            raise ValueError("The audio filter name is empty.")

        if not isinstance(enabled, bool):
            raise TypeError("The audio filter enabled state must be a boolean.")

        self._name = normalized_name
        self._enabled = enabled

    @property
    def name(self) -> str:
        """Return the public audio filter name.

        Returns:
            The normalized name used to identify the filter.
        """

        return self._name

    @property
    def enabled(self) -> bool:
        """Return whether the audio filter is enabled.

        Returns:
            ``True`` when the filter should be included in a filter chain.
        """

        return self._enabled

    @abstractmethod
    def build_expression(self) -> str:
        """Build the FFmpeg audio filter expression.

        Returns:
            The filter-specific FFmpeg expression.

        Raises:
            ValueError:
                The filter configuration cannot produce a valid expression.
        """

        raise NotImplementedError

    def render(self) -> str | None:
        """Return the active FFmpeg audio filter expression.

        Disabled filters return ``None`` without building their expression.

        Returns:
            The validated FFmpeg expression, or ``None`` when disabled.

        Raises:
            ValueError:
                The generated filter expression is empty or contains invalid
                control characters.
        """

        if not self._enabled:
            return None

        expression: str = self.build_expression().strip()
        self._validate_expression(expression)

        return expression

    def enable(self) -> Self:
        """Enable the audio filter.

        Returns:
            The filter instance for chained configuration.
        """

        self._enabled = True
        return self

    def disable(self) -> Self:
        """Disable the audio filter.

        Returns:
            The filter instance for chained configuration.
        """

        self._enabled = False
        return self

    def set_enabled(self, enabled: bool) -> Self:
        """Change whether the audio filter is enabled.

        Args:
            enabled:
                The new enabled state.

        Returns:
            The filter instance for chained configuration.

        Raises:
            TypeError:
                The supplied enabled state is not a boolean.
        """

        if not isinstance(enabled, bool):
            raise TypeError("The audio filter anabled state must be a boolean.")

        self._enabled = enabled
        return self

    def __bool__(self) -> bool:
        """Return whether the audio filter is enabled.

        Returns:
            ``True`` when the filter is currently enabled.
        """

        return self._enabled

    def __str__(self) -> str:
        """Return the rendered audio filter expression.

        Returns:
            The active expression, or an empty string when disabled.
        """

        return self.render() or ""

    @staticmethod
    def _validate_expression(expression: str) -> None:
        """Validate a generated FFmpeg filter expression.

        Args:
            expression:
                The generated FFmpeg expression to validate.

        Raises:
            ValueError:
                The expression is empty or contains invalid control characters.
        """

        if not expression:
            raise ValueError("The FFmpeg audio filter expression cannot be empty.")

        if "\x00" in expression or "\r" in expression or "\n" in expression:
            raise ValueError(
                "The FFmpeg audio filter expression contains an invalid "
                "control character."
            )

__all__: tuple[str, ...] = ("BaseAudioFilter",)
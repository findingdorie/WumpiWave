"""Custom FFmpeg audio filter used by WumpiWave.

This module provides a configurable audio filter for advanced FFmpeg
expressions that do not require a dedicated WumpiWave filter implementation.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from typing import Self

from .base import BaseAudioFilter

class CustomAudioFilter(BaseAudioFilter):
    """Represent a user-defined FFmpeg audio filter expression.

    The custom filter allows advanced FFmpeg audio filters to be added to an
    audio filter chain without creating a dedicated filter class. Expressions
    are validated when assigned and again before rendering.

    Attributes:
        name:
            The normalized public name used to identify the filter.
        enabled:
            Whether the filter is included in an active filter chain.
        expression:
            The configured FFmpeg audio filter expression.

    Methods:
        set_expression:
            Replace the configured FFmpeg expression.
        build_expression:
            Return the configured FFmpeg expression.
        _normalize_expression:
            Normalize and validate a custom FFmpeg expression.
    """

    __slots__ = ("_expression",)

    _expression: str

    def __init__(self, name: str, expression: str, *, enabled: bool = True) -> None:
        """Initialize a custom FFmpeg audio filter.

        Args:
            name:
                The public name used to identify the filter.
            expression:
                The FFmpeg audio filter expression to render.
            enabled:
                Whether the filter should initially be active.

        Raises:
            TypeError:
                The expression is not a string.
            ValueError:
                The filter name or expression is invalid.
        """

        super().__init__(
            name=name,
            enabled=enabled
        )

        self._expression = self._normalize_expression(expression)

    @property
    def expression(self) -> str:
        """Return the configured FFmpeg expression.

        Returns:
            The normalized custom audio filter expression.
        """

        return self._expression

    def set_expression(self, expression: str) -> Self:
        """Replace the configured FFmpeg expression.

        Args:
            expression:
                The new FFmpeg audio filter expression.

        Returns:
            The custom filter instance for chained configuration.

        Raises:
            TypeError:
                The supplied expression is not a string.
            ValueError:
                The supplied expression is empty or contains invalid control
                characters.
        """

        self._expression = self._normalize_expression(expression)
        return self

    def build_expression(self) -> str:
        """Return the configured FFmpeg audio filter expression.

        Returns:
            The current custom FFmpeg expression.
        """

        return self._expression

    @classmethod
    def _normalize_expression(cls, expression: str) -> str:
        """Normalize and validate a custom FFmpeg expression.

        Args:
            expression:
                The possible FFmpeg expression to normalize.

        Returns:
            The normalized non-empty expression.

        Raises:
            TypeError:
                The supplied expression is not a string.
            ValueError:
                The expression is empty or contains invalid control
                characters.
        """

        if not isinstance(expression, str):
            raise TypeError("The custom FFmpeg audio filter expression must be a string.")

        normalized_expression: str = expression.strip()
        cls._validate_expression(normalized_expression)

        return normalized_expression

__all__: tuple[str, ...] = ("CustomAudioFilter",)

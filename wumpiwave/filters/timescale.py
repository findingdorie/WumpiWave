"""Timescale audio filter used by WumpiWave.

This module provides independent playback speed and pitch adjustment through
FFmpeg-compatible audio filter expressions.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from math import isclose, isfinite
from typing import Self

from .base import BaseAudioFilter

class TimescaleFilter(BaseAudioFilter):
    """Adjust playback speed and pitch independently.

    The filter changes the input sample rate to apply a pitch adjustment,
    resamples the audio to its original sample rate, and compensates the
    resulting tempo through one or more FFmpeg ``atempo`` filters.

    Attributes:
        name:
            The normalized public name used to identify the filter.
        enabled:
            Whether the timescale filter is included in the active chain.
        speed:
            The target playback speed multiplier.
        pitch:
            The target pitch multiplier.
        sample_rate:
            The sample rate used for pitch processing.

    Methods:
        set_speed:
            Change the target playback speed.
        set_pitch:
            Change the target pitch multiplier.
        set_sample_rate:
            Change the sample rate used for pitch processing.
        reset:
            Restore the default speed and pitch values.
        build_expression:
            Build the FFmpeg timescale filter expression.
        _build_tempo_expressions:
            Split a tempo multiplier into supported FFmpeg expressions.
        _validate_multiplier:
            Validate and normalize a speed or pitch multiplier.
        _validate_sample_rate:
            Validate a sample rate.
    """

    __slots__ = (
        "_pitch",
        "_sample_rate",
        "_speed"
    )

    _DEFAULT_PITCH: float = 1.0
    _DEFAULT_SAMPLE_RATE: int = 48_000
    _DEFAULT_SPEED: float = 1.0
    _MAXIMUM_PITCH: float = 2.0
    _MAXIMUM_SPEED: float = 4.0
    _MINIMUM_PITCH: float = 0.5
    _MINIMUM_SPEED: float = 0.25
    _TEMPO_MAXIMUM: float = 2.0
    _TEMPO_MINIMUM: float = 0.5
    _TOLERANCE: float = 1e-9

    _pitch: float
    _sample_rate: int
    _speed: float

    def __init__(
        self,
        *,
        speed: float = _DEFAULT_SPEED,
        pitch: float = _DEFAULT_PITCH,
        sample_rate: int = _DEFAULT_SAMPLE_RATE,
        enabled: bool = True,
    ) -> None:
        """Initialize a timescale audio filter.

        Args:
            speed:
                The playback speed multiplier between ``0.25`` and ``4.0``.
            pitch:
                The pitch multiplier between ``0.5`` and ``2.0``.
            sample_rate:
                The positive sample rate used for pitch processing.
            enabled:
                Whether the filter should initially be active.

        Raises:
            TypeError:
                The sample rate is not an integer.
            ValueError:
                The speed, pitch, or sample rate is outside its supported
                range.
        """

        super().__init__(
            name="timescale",
            enabled=enabled
        )

        self._speed = self._validate_multiplier(
            speed,
            field_name="speed",
            minimum=self._MINIMUM_SPEED,
            maximum=self._MAXIMUM_SPEED,
        )
        self._pitch = self._validate_multiplier(
            pitch,
            field_name="pitch",
            minimum=self._MINIMUM_PITCH,
            maximum=self._MAXIMUM_PITCH
        )
        self._sample_rate = self._validate_sample_rate(sample_rate)

    @property
    def speed(self) -> float:
        """Return the target playback speed.

        Returns:
            The configured playback speed multiplier.
        """

        return self._speed

    @property
    def pitch(self) -> float:
        """Return the target pitch multiplier.

        Returns:
            The configured pitch multiplier.
        """

        return self._pitch

    @property
    def sample_rate(self) -> int:
        """Return the sample rate used for pitch processing.

        Returns:
            The configured sample rate in hertz.
        """

        return self._sample_rate

    def set_speed(self, speed: float) -> Self:
        """Change the target playback speed.

        Args:
            speed:
                The playback speed multiplier between ``0.25`` and ``4.0``.

        Returns:
            The filter instance for chained configuration.

        Raises:
            ValueError:
                The supplied speed is not finite or outside the supported
                range.
        """

        self._speed = self._validate_multiplier(
            speed,
            field_name="speed",
            minimum=self._MINIMUM_SPEED,
            maximum=self._MAXIMUM_SPEED
        )

        return self

    def set_pitch(self, pitch: float) -> Self:
        """Change the target pitch multiplier.

        Args:
            pitch:
                The pitch multiplier between ``0.5`` and ``2.0``.

        Returns:
            The filter instance for chained configuration.

        Raises:
            ValueError:
                The supplied pitch is not finite or outside the supported
                range.
        """

        self._pitch = self._validate_multiplier(
            pitch,
            field_name="pitch",
            minimum=self._MINIMUM_PITCH,
            maximum=self._MAXIMUM_PITCH
        )

        return self

    def set_sample_rate(self, sample_rate: int) -> Self:
        """Change the sample rate used for pitch processing.

        Args:
            sample_rate:
                The positive sample rate in hertz.

        Returns:
            The filter instance for chained configuration.

        Raises:
            TypeError:
                The supplied sample rate is not an integer.
            ValueError:
                The supplied sample rate is not positive.
        """

        self._sample_rate = self._validate_sample_rate(sample_rate)
        return self

    def reset(self) -> Self:
        """Restore the default speed and pitch values.

        The configured sample rate and enabled state remain unchanged.

        Returns:
            The filter instance for chained configuration.
        """

        self._speed = self._DEFAULT_SPEED
        self._pitch = self._DEFAULT_PITCH

        return self

    def build_expression(self) -> str:
        """Build the FFmpeg timescale filter expression.

        Pitch processing is omitted when the pitch multiplier equals ``1.0``.
        Tempo processing is omitted when no speed compensation is required.

        Returns:
            The complete comma-separated FFmpeg audio filter expression.
        """

        expressions: list[str] = []
        pitch_changed: bool = not isclose(
            self._pitch,
            self._DEFAULT_PITCH,
            rel_tol=0.0,
            abs_tol=self._TOLERANCE
        )

        if pitch_changed:
            adjusted_sample_rate: int = round(self._sample_rate * self._pitch)

            expressions.extend(
                (
                    f"asetrate={adjusted_sample_rate}",
                    f"aresample={self._sample_rate}"
                )
            )

        tempo_multiplier: float = (
            self._speed / self._pitch
            if pitch_changed
            else self._speed
        )
        expressions.extend(self._build_tempo_expression(tempo_multiplier))

        if not expressions:
            return "anull"

        return ",".join(expressions)

    @classmethod
    def _build_tempo_expression(cls, tempo_multiplier: float) -> tuple[str, ...]:
        """Split a tempo multiplier into supported FFmpeg expressions.

        Every generated multiplier remains between ``0.5`` and ``2.0``.
        Multiplying the generated values produces the requested total tempo.

        Args:
            tempo_multiplier:
                The total tempo adjustment to represent.

        Returns:
            The ordered FFmpeg ``atempo`` expressions.
        """

        remaining_multiplier: float = tempo_multiplier
        tempo_factors: list[float] = []

        while remaining_multiplier > (
                cls._TEMPO_MAXIMUM + cls._TOLERANCE
        ):
            tempo_factors.append(cls._TEMPO_MAXIMUM)
            remaining_multiplier /= cls._TEMPO_MAXIMUM

        while remaining_multiplier < (
                cls._TEMPO_MINIMUM - cls._TOLERANCE
        ):
            tempo_factors.append(cls._TEMPO_MINIMUM)
            remaining_multiplier /= cls._TEMPO_MINIMUM

        if not isclose(
                remaining_multiplier,
                1.0,
                rel_tol=0.0,
                abs_tol=cls._TOLERANCE
        ):
            tempo_factors.append(remaining_multiplier)

        return tuple(
            f"atempo={tempo_factor:.10g}"
            for tempo_factor in tempo_factors
        )

    @staticmethod
    def _validate_multiplier(
            multiplier: float,
            *,
            field_name: str,
            minimum: float,
            maximum: float,
    ) -> float:
        """Validate and normalize a speed or pitch multiplier.

        Args:
            multiplier:
                The numeric multiplier to validate.
            field_name:
                The human-readable field name used in error messages.
            minimum:
                The smallest supported multiplier.
            maximum:
                The largest supported multiplier.

        Returns:
            The validated multiplier as a float.

        Raises:
            ValueError:
                The multiplier is not finite or outside the supported range.
        """

        if (
            isinstance(multiplier, bool)
            or not isfinite(multiplier)
            or not minimum <= multiplier <= maximum
        ):
            raise ValueError(
                f"The timescale {field_name} must be between "
                f"{minimum:g} and {maximum:g}."
            )

        return float(multiplier)

    @staticmethod
    def _validate_sample_rate(sample_rate: int) -> int:
        """Validate a sample rate.

        Args:
            sample_rate:
                The sample rate in hertz to validate.

        Returns:
            The validated positive sample rate.

        Raises:
            TypeError:
                The supplied sample rate is not an integer.
            ValueError:
                The supplied sample rate is not positive.
        """

        if isinstance(sample_rate, bool) or not isinstance(sample_rate, int):
            raise TypeError("The timescale sample rate must be an integer.")

        if sample_rate <= 0:
            raise ValueError("The timescale sample rate must be greater than zero.")

        return sample_rate

__all__: tuple[str, ...] = ("TimescaleFilter",)
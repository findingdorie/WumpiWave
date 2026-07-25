"""Parametric equalizer audio filter used by WumpiWave.

This module provides validated equalizer bands and renders them into
FFmpeg-compatible audio filter expressions.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from math import isfinite
from typing import Self

from .base import BaseAudioFilter

@dataclass(frozen=True, slots=True)
class EqualizerBand:
    """Represent one parametric equalizer frequency band.

    Positive gain values amplify the selected frequency range, while negative
    values attenuate it. The width is represented as a Q factor.

    Attributes:
        frequency:
            The center frequency of the band in hertz.
        gain:
            The gain applied to the band in decibels.
        width:
            The positive Q factor controlling the affected frequency range.

    Methods:
        __post_init__:
            Validate the equalizer band configuration.
        render:
            Render the band as an FFmpeg equalizer expression.
    """

    frequency: float
    gain: float
    width: float = 1.0

    def __post_init__(self) -> None:
        """Validate the equalizer band configuration.

        Raises:
            ValueError:
                The frequency, gain, or width is invalid.
        """

        if not isfinite(self.frequency) or self.frequency <= 0.0:
            raise ValueError("The equalizer frequency must be finite and greater than zero.")

        if not isfinite(self.gain):
            raise ValueError("The equalizer gain must be finite.")

        if not isfinite(self.width) or self.width <= 0.0:
            raise ValueError("The equalizer width must be finite and greater than zero.")

    def render(self) -> str:
        """Render the band as an FFmpeg equalizer expression.

        Returns:
            The FFmpeg expression representing this frequency band.
        """

        return (
            f"equalizer="
            f"f={self.frequency:g}:"
            f"t=q:"
            f"w={self.width:g}:"
            f"g={self.gain:g}"
        )

class EqualizerFilter(BaseAudioFilter):
    """Apply multiple parametric equalizer bands during playback.

    Bands are rendered in their current order and joined into one FFmpeg audio
    filter chain. At least one band must exist while the filter is enabled and
    rendered.

    Attributes:
        name:
            The normalized public name used to identify the filter.
        enabled:
            Whether the equalizer is included in an active filter chain.
        bands:
            An immutable snapshot of the configured equalizer bands.
        band_count:
            The number of configured equalizer bands.

    Methods:
        add:
            Append one equalizer band.
        extend:
            Append multiple equalizer bands atomically.
        get:
            Return an equalizer band by index.
        replace:
            Replace an equalizer band by index.
        remove:
            Remove and return an equalizer band by index.
        clear:
            Remove and return every equalizer band.
        build_expression:
            Render all configured bands into one FFmpeg expression.
        __getitem__:
            Return an equalizer band or immutable band slice.
        __iter__:
            Iterate over configured equalizer bands.
        __len__:
            Return the number of configured equalizer bands.
        _validate_band:
            Validate a possible equalizer band.
        _normalize_index:
            Normalize and validate a band index.
    """

    __slots__ = ("_bands",)

    _bands: list[EqualizerBand]

    def __init__(self, bands: Iterable[EqualizerBand] = (), *, enabled: bool = True) -> None:
        """Initialize a parametric equalizer filter.

        Args:
            bands:
                The equalizer bands configured during initialization.
            enabled:
                Whether the equalizer should initially be active.

        Raises:
            TypeError:
                A supplied value is not an equalizer band.
        """

        super().__init__(
            name="equalizer",
            enabled=enabled
        )

        self._bands = []
        self.extend(bands)

    @property
    def bands(self) -> tuple[EqualizerBand, ...]:
        """Return an immutable snapshot of equalizer bands.

        Returns:
            The bands in their current rendering order.
        """

        return tuple(self._bands)

    @property
    def band_count(self) -> int:
        """Return the number of configured equalizer bands.

        Returns:
            The current equalizer band count.
        """

        return len(self._bands)

    def add(self, band: EqualizerBand) -> Self:
        """Append one equalizer band.

        Args:
            band:
                The equalizer band to append.

        Returns:
            The equalizer filter for chained configuration.

        Raises:
            TypeError:
                The supplied value is not an equalizer band.
        """

        self._validate_band(band)
        self._bands.append(band)

        return self

    def extend(self, bands: Iterable[EqualizerBand]) -> Self:
        """Append multiple equalizer bands atomically.

        Every supplied band is validated before the equalizer is modified.

        Args:
            bands:
                The equalizer bands to append.

        Returns:
            The equalizer filter for chained configuration.

        Raises:
            TypeError:
                A supplied value is not an equalizer band.
        """

        new_bands: tuple[EqualizerBand, ...] = tuple(bands)

        for band in new_bands:
            self._validate_band(band)

        self._bands.extend(new_bands)
        return self

    def get(self, index: int) -> EqualizerBand:
        """Return an equalizer band by index.

        Negative indexes follow normal Python indexing behavior.

        Args:
            index:
                The equalizer band index to retrieve.

        Returns:
            The band stored at the normalized index.

        Raises:
            IndexError:
                The supplied index is outside the configured bands.
        """

        return self._bands[self._normalize_index(index)]

    def replace(self, index: int, band: EqualizerBand):
        """Replace an equalizer band by index.

        Args:
            index:
                The index of the band to replace.
            band:
                The replacement equalizer band.

        Returns:
            The equalizer band that was replaced.

        Raises:
            IndexError:
                The supplied index is outside the configured bands.
            TypeError:
                The supplied value is not an equalizer band.
        """

        self._validate_band(band)

        normalized_index: int = self._normalize_index(index)
        previous_band: EqualizerBand = self._bands[normalized_index]
        self._bands[normalized_index] = band

        return previous_band

    def remove(self, index: int) -> EqualizerBand:
        """Remove and return an equalizer band by index.

        Args:
            index:
                The index of the equalizer band to remove.

        Returns:
            The removed equalizer band.

        Raises:
            IndexError:
                The supplied index is outside the configured bands.
        """

        return self._bands.pop(self._normalize_index(index))

    def clear(self) -> tuple[EqualizerBand, ...]:
        """Remove and return every equalizer band.

        Returns:
            The removed bands in their previous rendering order.
        """

        removed_bands: tuple[EqualizerBand, ...] = tuple(self._bands)
        self._bands.clear()

        return removed_bands

    def build_expression(self) -> str:
        """Render all configured bands into one FFmpeg expression.

        Returns:
            The comma-separated FFmpeg equalizer expressions.

        Raises:
            ValueError:
                No equalizer bands are configured.
        """

        if not self._bands:
            raise ValueError("At least one equalizer band is required to render the filter.")

        return ",".join(band.render() for band in self._bands)

    def __getitem__(self, index: int | slice) -> EqualizerBand | tuple[EqualizerBand, ...]:
        """Return an equalizer band or immutable band slice.

        Args:
            index:
                The integer index or slice to retrieve.

        Returns:
            One equalizer band or an immutable tuple of bands.

        Raises:
            IndexError:
                An integer index is outside the configured bands.
        """

        if isinstance(index, slice):
            return tuple(self._bands[index])

        return self.get(index)

    def __iter__(self) -> Iterator[EqualizerBand]:
        """Iterate over configured equalizer bands.

        Returns:
            An iterator following the current rendering order.
        """

        return iter(tuple(self._bands))

    def __len__(self) -> int:
        """Return the number of configured equalizer bands.

        Returns:
            The current equalizer band count.
        """

        return len(self._bands)

    @staticmethod
    def _validate_band(band: EqualizerBand) -> None:
        """Validate a possible equalizer band.

        Args:
            band:
                The value to validate.

        Raises:
            TypeError:
                The supplied value is not an equalizer band.
        """

        if not isinstance(band, EqualizerBand):
            raise TypeError("The equalizer only accepts EqualizerBand instances.")

    def _normalize_index(self, index: int) -> int:
        """Normalize and validate an equalizer band index.

        Args:
            index:
                The positive or negative band index to normalize.

        Returns:
            The equivalent non-negative band index.

        Raises:
            IndexError:
                The supplied index is outside the configured bands.
        """

        band_count: int = len(self._bands)
        normalized_index: int = index

        if normalized_index < 0:
            normalized_index += band_count

        if not 0 <= normalized_index < band_count:
            raise IndexError(
                f"Equalizer band index {index} is outside a filter containing "
                f"{band_count} bands."
            )

        return normalized_index

__all__: tuple[str, ...] = (
    "EqualizerBand",
    "EqualizerFilter"
)
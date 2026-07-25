"""FFmpeg audio source creation used by WumpiWave Discord backends.

This module converts resolved WumpiWave playable sources into Discord-compatible
PCM audio sources with seeking, HTTP headers, reconnection settings, and
runtime volume control.

Attributes:
    DiscordPCMSource:
        A Discord PCM volume transformer wrapping an FFmpeg audio source.

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from math import isfinite
from shlex import join
from typing import Self
from urllib.parse import SplitResult, urlsplit

from discord import FFmpegPCMAudio, PCMVolumeTransformer
from ..filters import AudioFilterChain

from ..models import PlayableSource

type DiscordPCMSource = PCMVolumeTransformer[FFmpegPCMAudio]

class FFmpegAudioSourceFactory:
    """Create Discord-compatible FFmpeg audio sources.

    The factory converts temporary playable stream URLs into PCM audio sources
    that Discord can encode and transmit. Network streams may use automatic
    reconnection, while supplied HTTP headers are forwarded to FFmpeg.

    FFmpeg processes are started when a source is created. The returned Discord
    audio source owns the process and releases it through its cleanup method.

    Attributes:
        executable:
            The FFmpeg executable name or filesystem path.
        reconnect:
            Whether HTTP and HTTPS streams use FFmpeg reconnection options.
        reconnect_delay_max:
            The maximum delay between reconnection attempts in seconds.
        extra_before_options:
            Additional FFmpeg arguments inserted before the input.
        extra_options:
            Additional FFmpeg arguments inserted after the input.

    Methods:
        create:
            Create a volume-controlled Discord PCM audio source.
        _build_before_options:
            Build FFmpeg arguments placed before the input.
        _build_options:
            Build FFmpeg arguments placed after the input.
        _format_headers:
            Convert HTTP headers into the format expected by FFmpeg.
        _is_network_source:
            Determine whether a source uses HTTP or HTTPS.
        _normalize_arguments:
            Normalize additional FFmpeg argument tokens.
        _validate_start_position:
            Validate a playback start position.
        _validate_volume:
            Validate a Discord PCM playback volume.
    """

    __slots__ = (
        "_executable",
        "_extra_before_options",
        "_extra_options",
        "_filter_chain",
        "_reconnect",
        "_reconnect_delay_max"
    )

    _MAXIMUM_VOLUME: float = 2.0
    _NETWORK_SCHEMES: frozenset[str] = frozenset(
        {
            "http",
            "https"
        }
    )

    _executable: str
    _extra_before_options: tuple[str, ...]
    _extra_options: tuple[str, ...]
    _filter_chain: AudioFilterChain
    _reconnect: bool
    _reconnect_delay_max: int

    def __init__(
            self,
            *,
            executable: str = "ffmpeg",
            reconnect: bool = True,
            reconnect_delay_max: int = 5,
            filter_chain: AudioFilterChain | None = None,
            extra_before_options: Iterable[str] = (),
            extra_options: Iterable[str] = (),
    ) -> None:
        """Initialize an FFmpeg audio source factory.

        Args:
            executable:
                The FFmpeg executable name or filesystem path.
            reconnect:
                Whether network streams use FFmpeg reconnection options.
            reconnect_delay_max:
                The maximum delay between reconnection attempts in seconds.
            extra_before_options:
                Additional individual FFmpeg arguments inserted before the
                input argument.
            extra_options:
                Additional individual FFmpeg arguments inserted after the
                input argument.

        Raises:
            TypeError:
                Additional FFmpeg arguments were supplied as one string.
            ValueError:
                The executable, reconnection delay, or an argument is invalid.
        """

        normalized_executable = executable.strip()

        if normalized_executable:
            raise ValueError("The FFmpeg executable cannot be empty.")

        if (
            isinstance(reconnect_delay_max, bool)
            or reconnect_delay_max < 0
        ):
            raise ValueError("The FFmpeg reconnection delay must be a non-negative integer.")

        self._executable = normalized_executable
        self._reconnect = reconnect
        self._reconnect_delay_max = reconnect_delay_max
        self._filter_chain = (
            AudioFilterChain()
            if filter_chain is None
            else self._validate_filter_chain(filter_chain)
        )
        self._extra_before_options = self._normalize_arguments(
            extra_options,
            argument_group="after-input"
        )

    @property
    def executable(self) -> str:
        """Return the configured FFmpeg executable.

        Returns:
            The executable name or filesystem path used to start FFmpeg.
        """

        return self._executable

    @property
    def reconnect(self) -> bool:
        """Return whether network reconnection is enabled.

        Returns:
            ``True`` when HTTP and HTTPS sources use reconnection options.
        """

        return self._reconnect

    @property
    def reconnect_delay_max(self) -> int:
        """Return the maximum FFmpeg reconnection delay.

        Returns:
            The maximum delay between reconnection attempts in seconds.
        """

        return self._reconnect_delay_max

    @property
    def filter_chain(self) -> AudioFilterChain:
        """Return the configured audio filter chain.

        Returns:
            The mutable filter chain used for newly created audio sources.
        """

        return self._filter_chain

    @property
    def filter_expression(self) -> str | None:
        """Return the currently rendered audio filter expression.

        Returns:
            The FFmpeg filter expression, or ``None`` when no filters are active.
        """

        return self._filter_chain.render()

    @property
    def extra_before_options(self) -> tuple[str, ...]:
        """Return additional FFmpeg before-input arguments.

        Returns:
            The immutable configured argument tokens.
        """

        return self._extra_before_options

    @property
    def extra_options(self) -> tuple[str, ...]:
        """Return additional FFmpeg after-input arguments.

        Returns:
            The immutable configured argument tokens.
        """

        return self._extra_options

    def create(self, source: PlayableSource, *, start_position: float = 0.0, volume: float = 1.0) -> DiscordPCMSource:
        """Create a volume-controlled Discord PCM audio source.

        Args:
            source:
                The resolved playable source passed to FFmpeg.
            start_position:
                The initial playback position in seconds.
            volume:
                The initial playback volume between ``0.0`` and ``2.0``.

        Returns:
            A Discord PCM audio source with runtime volume control.

        Raises:
            ValueError:
                The start position, volume, or HTTP headers are invalid.
            discord.ClientException:
                The FFmpeg process could not be created.
        """

        normalized_start_position: float = (self._validate_start_position(start_position))
        normalized_volume: float = self._validate_volume(volume)
        ffmpeg_source = FFmpegPCMAudio(
            source.stream_url,
            executable=self._executable,
            before_options=self._build_before_options(
                source,
                start_position=normalized_start_position
            ),
            options=self._build_options()
        )

        try:
            return PCMVolumeTransformer(
                ffmpeg_source,
                volume=normalized_volume
            )
        except BaseException:
            ffmpeg_source.cleanup()
            raise

    def _build_before_options(self, source: PlayableSource, *, start_position: float) -> str:
        """Build FFmpeg arguments placed before the input.

        Args:
            source:
                The playable source whose input options should be constructed.
            start_position:
                The validated initial playback position in seconds.

        Returns:
            A shell-compatible argument string parsed internally by discord.py.

        Raises:
            ValueError:
                A source HTTP header contains an invalid name or value.
        """

        arguments: list[str] = ["-nostdin"]

        if self._reconnect and self._is_network_source(source.stream_url):
            arguments.extend(
                (
                    "-reconnect",
                    "1",
                    "-reconnect_streamed",
                    "1",
                    "-reconnect_delay_max",
                    str(self._reconnect_delay_max)
                )
            )

        if start_position > 0.0:
            arguments.extend(
                (
                    "-ss",
                    f"{start_position:.3f}"
                )
            )

        formatted_headers: str | None = self._format_headers(source.headers)

        if formatted_headers is not None:
            arguments.extend(
                (
                    "-headers",
                    formatted_headers
                )
            )

        arguments.extend(self._extra_before_options)

        return join(arguments)

    def set_filter_chain(
            self,
            filter_chain: AudioFilterChain | None,
    ) -> Self:
        """Replace the configured audio filter chain.

        Args:
            filter_chain:
                The new filter chain, or ``None`` to use an empty chain.

        Returns:
            The source factory for chained configuration.

        Raises:
            TypeError:
                The supplied value is not an audio filter chain.
        """

        self._filter_chain = (
            AudioFilterChain()
            if filter_chain is None
            else self._validate_filter_chain(filter_chain)
        )

        return self

    def _build_options(self) -> str:
        """Build FFmpeg arguments placed after the input.

        Returns:
            The complete FFmpeg after-input argument string.
        """

        arguments: list[str] = [
            "-vn",
            "-sn",
            "-dn",
        ]
        filter_expression: str | None = self._filter_chain.render()

        if filter_expression is not None:
            arguments.extend(
                (
                    "-af",
                    filter_expression
                )
            )

        arguments.extend(self._extra_options)

        return join(arguments)

    @staticmethod
    def _format_headers(headers: Mapping[str, str]) -> str | None:
        """Convert HTTP headers into the format expected by FFmpeg.

        Args:
            headers:
                The HTTP headers attached to a playable source.

        Returns:
            The CRLF-separated header block, or ``None`` when no headers exist.

        Raises:
            ValueError:
                A header name is empty or a header contains prohibited
                characters.
        """

        if not headers:
            return None

        formatted_headers: list[str] = []

        for header_name, header_value in headers.items():
            normalized_name: str = header_name.strip()
            normalized_value: str = header_value.strip()

            if not normalized_name:
                raise ValueError("FFmpeg HTTP header names cannot be empty.")

            if (
                ":" in normalized_name
                or "\r" in normalized_name
                or "\n" in normalized_name
            ):
                raise ValueError(f"FFmpeg HTTP header {normalized_name!r} contains an invalid line break.")

            formatted_headers.append(f"{normalized_name}: {normalized_value}")

        return "\r\n".join(formatted_headers) + "\r\n"

    @classmethod
    def _is_network_source(cls, stream_url: str) -> bool:
        """Determine whether a source uses HTTP or HTTPS.

        Args:
            stream_url:
                The playable stream URL to inspect.

        Returns:
            ``True`` when the URL uses a supported network scheme.
        """

        try:
            parsed_url: SplitResult = urlsplit(stream_url)
        except ValueError:
            return False

        return parsed_url.scheme.casefold() in cls._NETWORK_SCHEMES

    @staticmethod
    def _normalize_arguments(arguments: Iterable[str], *, argument_group: str) -> tuple[str, ...]:
        """Normalize additional FFmpeg argument tokens.

        Args:
            arguments:
                The individual FFmpeg argument tokens to normalize.
            argument_group:
                The human-readable argument group used in error messages.

        Returns:
            The immutable normalized argument tokens.

        Raises:
            TypeError:
                The arguments were supplied as one string.
            ValueError:
                One of the supplied arguments is empty.
        """

        if isinstance(arguments, str):
            raise TypeError(
                "Additional FFmpeg arguments must be supplied as an iterable "
                "of individual argument tokens."
            )

        normalized_arguments: list[str] = []

        for argument in arguments:
            normalized_argument: str = argument.strip()

            if not normalized_argument:
                raise ValueError(f"FFmpeg {argument_group} cannot be empty.")

            normalized_arguments.append(normalized_argument)

        return tuple(normalized_arguments)

    @staticmethod
    def _validate_start_position(start_position: float) -> float:
        """Validate a playback start position.

        Args:
            start_position:
                The initial playback position in seconds.

        Returns:
            The validated position as a float.

        Raises:
            ValueError:
                The position is negative or not finite.
        """

        if not isfinite(start_position) or start_position < 0.0:
            raise ValueError("The FFmpeg start posiition must be finite and non-negative.")

        return float(start_position)

    @classmethod
    def _validate_volume(cls, volume: float) -> float:
        """Validate a Discord PCM playback volume.

        Args:
            volume:
                The initial volume applied to the PCM audio source.

        Returns:
            The validated volume as a float.

        Raises:
            ValueError:
                The volume is not between ``0.0`` and ``2.0``.
        """

        if (
            not isfinite(volume)
            or not 0.0 <= volume <= cls._MAXIMUM_VOLUME
        ):
            raise ValueError("The Discord playback volume must be between 0.0 and 2.0.")

        return float(volume)

    @staticmethod
    def _validate_filter_chain(
            filter_chain: AudioFilterChain,
    ) -> AudioFilterChain:
        """Validate a possible audio filter chain.

        Args:
            filter_chain:
                The value to validate.

        Returns:
            The validated audio filter chain.

        Raises:
            TypeError:
                The supplied value is not an audio filter chain.
        """

        if not isinstance(filter_chain, AudioFilterChain):
            raise TypeError(
                "The FFmpeg filter chain must be an AudioFilterChain instance."
            )

        return filter_chain

__all__: tuple[str, ...] = (
    "DiscordPCMSource",
    "FFmpegAudioSourceFactory"
)
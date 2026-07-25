"""Direct HTTP stream resolver used by WumpiWave.

This module converts normalized HTTP media tracks into playable audio sources
without performing provider-specific extraction.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import SplitResult, urlsplit

from ..exceptions import StreamNotFoundError, UnsupportedMediaError
from ..models import MediaSource, MediaTrack, PlayableSource
from .base import BaseStreamResolver

class HTTPResolver(BaseStreamResolver):
    """Resolve direct HTTP media tracks into playable audio sources.

    The resolver treats the public track URL as the playable stream URL after
    validating its scheme and hostname. Optional HTTP headers can be attached
    to every generated source.

    No network request is performed during resolution. Stream availability and
    supported audio formats remain the responsibility of the playback backend.

    Attributes:
        name:
            The normalized public resolver name.
        closed:
            Whether the resolver has released its resources.
        headers:
            The immutable HTTP headers attached to resolved sources.
        seekable:
            Whether resolved HTTP sources should support seeking.

    Methods:
        supports:
            Determine whether the resolver supports a media track.
        resolve:
            Convert an HTTP track into a playable audio source.
        _normalize_headers:
            Normalize and validate configured HTTP headers.
        _validate_stream_url:
            Validate and normalize a direct HTTP stream URL.
        _close:
            Release resolver-specific resources.
    """

    __slots__ = (
        "_headers",
        "_seekable"
    )

    _SUPPORTED_SCHEMES: frozenset[str] = frozenset(
        {
            "http",
            "https"
        }
    )

    _headers: dict[str, str]
    _seekable: bool

    def __init__(self, *, headers: Mapping[str, str] | None = None, seekable: bool = True) -> None:
        """Initialize a direct HTTP stream resolver.

        Args:
            headers:
                Optional HTTP headers attached to every resolved source.
            seekable:
                Whether generated playable sources should support seeking.

        Raises:
            ValueError:
                A supplied HTTP header name is empty.
        """

        super().__init__(name="http")

        self._headers = self._normalize_headers(headers or {})
        self._seekable = seekable

    @property
    def headers(self) -> Mapping[str, str]:
        """Return the configured HTTP headers.

        Returns:
            A copy of the headers attached to resolved playable sources.
        """

        return self._headers.copy()

    @property
    def seekable(self) -> bool:
        """Return whether resolved HTTP sources support seeking.

        Returns:
            The configured seeking behavior.
        """

        return self._seekable

    def supports(self, track: MediaTrack) -> bool:
        """Return whether the resolver supports a media track.

        Args:
            track:
                The normalized media track to inspect.

        Returns:
            ``True`` when the track originates from a valid HTTP or HTTPS URL
            and the resolver remains open, otherwise ``False``.
        """

        if self.closed or track.source is not MediaSource.HTTP:
            return False

        return self._validate_stream_url(track.url) is not None

    async def resolve(self, track: MediaTrack) -> PlayableSource:
        """Resolve a direct HTTP track into a playable audio source.

        Args:
            track:
                The normalized HTTP media track to resolve.

        Returns:
            A playable source containing the direct stream URL and configured
            request headers.

        Raises:
            UnsupportedMediaError:
                The supplied track does not originate from HTTP.
            StreamNotFoundError:
                The track URL is not a valid HTTP or HTTPS stream URL.
        """

        self._ensure_open()

        if track.source is not MediaSource.HTTP:
            raise UnsupportedMediaError(track=track)

        stream_url: str | None = self._validate_stream_url(track.url)

        if stream_url is None:
            raise StreamNotFoundError(
                resolver_name=self.name,
                track=track
            )

        return PlayableSource(
            stream_url=stream_url,
            source=MediaSource.HTTP,
            headers=self._headers,
            seekable=self._seekable and not track.is_live
        )

    @staticmethod
    def _normalize_headers(headers: Mapping[str, str]) -> dict[str, str]:
        """Normalize and validate configured HTTP headers.

        Args:
            headers:
                The HTTP headers to normalize.

        Returns:
            The normalized header mapping.

        Raises:
            ValueError:
                A supplied HTTP header name is empty.
        """

        normalized_headers: dict[str, str] = {}

        for header_name, header_value in headers.items():
            normalized_header_name: str = header_name.strip()

            if not normalized_header_name:
                raise ValueError("HTTP header names cannot be empty.")

            normalized_headers[normalized_header_name] = header_value.strip()

        return normalized_headers

    @classmethod
    def _validate_stream_url(cls, stream_url: str) -> str | None:
        """Validate and normalize a direct HTTP stream URL.

        Args:
            stream_url:
                The possible direct stream URL to validate.

        Returns:
            The normalized URL, or ``None`` when it is invalid.
        """

        normalized_stream_url: str = stream_url.strip()

        if not normalized_stream_url:
            return None

        try:
            parsed_stream_url: SplitResult = urlsplit(normalized_stream_url)
        except ValueError:
            return None

        if parsed_stream_url.scheme.casefold() not in cls._SUPPORTED_SCHEMES:
            return None

        if parsed_stream_url.hostname is None:
            return None

        if any(character.isspace() for character in parsed_stream_url.netloc):
            return None

        return normalized_stream_url

    async def _close(self) -> None:
        """Release resolver-specific resources."""

__all__: tuple[str, ...] = ("HTTPResolver",)
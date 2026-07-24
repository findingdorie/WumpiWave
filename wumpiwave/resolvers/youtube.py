"""YouTube stream resolver used by WumpiWave.

This module converts normalized YouTube tracks into temporary playable audio
sources by extracting direct stream information with yt-dlp.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from asyncio import Semaphore, to_thread
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import cast
from urllib.parse import parse_qs, urlsplit

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from ..exceptions import (
    ResolverError,
    StreamNotFoundError,
    UnsupportedMediaError,
)
from ..models import MediaSource, MediaTrack, PlayableSource
from .base import BaseStreamResolver

class YouTubeResolver(BaseStreamResolver):
    """Resolve YouTube tracks into temporary playable audio sources.

    The resolver uses yt-dlp to extract a direct audio stream URL and any HTTP
    headers required to access it. Extraction runs in a worker thread because
    yt-dlp exposes a synchronous Python interface.

    A new yt-dlp extractor instance is created for every resolution operation.
    Concurrent extractions are limited to avoid excessive CPU, network, and
    external service usage.

    Attributes:
        name:
            The normalized public resolver name.
        closed:
            Whether the resolver has released its resources.
        format_selector:
            The yt-dlp format expression used to select an audio stream.
        maximum_concurrency:
            The maximum number of simultaneous extraction operations.

    Methods:
        supports:
            Determine whether the resolver supports a media track.
        resolve:
            Convert a YouTube track into a playable audio source.
        _extract_information:
            Extract and sanitize stream information with yt-dlp.
        _extract_stream_url:
            Extract and validate the direct stream URL.
        _extract_headers:
            Extract normalized HTTP headers from stream information.
        _extract_expiration:
            Extract an expiration timestamp from the stream URL.
        _close:
            Release resolver-specific resources.
    """

    __slots__ = (
        "_extractor_options",
        "_format_selector",
        "_maximum_concurrency",
        "_semaphore"
    )

    _DEFAULT_FORMAT_SELECTOR: str = "bestaudio/best"
    _EXPIRATION_PARAMETERS: tuple[str, ...] = (
        "expire",
        "expires",
        "exp"
    )

    _extractor_options: dict[str, object]
    _format_selector: str
    _maximum_concurrency: int
    _semaphore: Semaphore

    def __init__(
            self,
            *,
            format_selector: str = _DEFAULT_FORMAT_SELECTOR,
            maximum_concurrency: int = 2,
            cookies_file: str | None = None,
            extractor_options: Mapping[str, object] | None = None
    ) -> None:
        """Initialize a YouTube stream resolver.

        Args:
            format_selector:
                The yt-dlp format expression used to select an audio stream.
            maximum_concurrency:
                The maximum number of simultaneous extraction operations.
            cookies_file:
                An optional path to a Netscape-formatted cookies file.
            extractor_options:
                Additional yt-dlp options applied to every extraction.

        Raises:
            ValueError:
                The format selector, concurrency limit, or cookies path is
                invalid.
        """

        normalized_format_selector: str = format_selector.strip()
        normalized_cookies_file: str | None = (cookies_file.strip() if cookies_file is not None else None)

        if not normalized_format_selector:
            raise ValueError("The YouTube format selector cannot be empty.")

        if maximum_concurrency <= 0:
            raise ValueError("The maximum resolver concurrency must be greater than zero.")

        if normalized_cookies_file == "":
            raise ValueError("The YouTube cookies file path cannot be empty.")

        super().__init__(name="youtube")

        self._format_selector = normalized_format_selector
        self._maximum_concurrency = maximum_concurrency
        self._semaphore = Semaphore(maximum_concurrency)
        self._extractor_options = dict(extractor_options or {})

        self._extractor_options["format"] = normalized_format_selector
        self._extractor_options["noplaylist"] = True
        self._extractor_options["skip_download"] = True
        self._extractor_options.setdefault("quiet", True)
        self._extractor_options.setdefault("no_warnings", True)

        if normalized_cookies_file is not None:
            self._extractor_options["cookiefile"] = normalized_cookies_file

    @property
    def format_selector(self) -> str:
        """Return the configured yt-dlp format selector.

        Returns:
            The format expression used to select an audio stream.
        """

        return self._format_selector

    @property
    def maximum_concurrency(self) -> int:
        """Return the maximum number of simultaneous extractions.

        Returns:
            The configured extraction concurrency limit.
        """

        return self._maximum_concurrency

    def supports(self, track: MediaTrack) -> bool:
        """Return whether the resolver supports a media track.

        Args:
            track:
                The normalized media track to inspect.

        Returns:
            ``True`` when the track originates from YouTube and the resolver
            remains open, otherwise ``False``.
        """

        return not self.closed and track.source is MediaSource.YOUTUBE

    async def resolve(self, track: MediaTrack) -> PlayableSource:
        """Resolve a YouTube track into a playable audio source.

        Args:
            track:
                The normalized YouTube track to resolve.

        Returns:
            A temporary playable source containing the direct stream URL,
            required HTTP headers, expiration time, and seeking support.

        Raises:
            ResolverError:
                yt-dlp failed unexpectedly while extracting stream information.
            StreamNotFoundError:
                No playable audio stream could be extracted.
            UnsupportedMediaError:
                The supplied track does not originate from YouTube.
        """

        self._ensure_open()

        if not self.supports(track):
            raise UnsupportedMediaError(track=track)

        try:
            async with self._semaphore:
                information: dict[str, object] = await to_thread(
                    self._extract_information,
                    track.url
                )
        except DownloadError as exception:
            raise StreamNotFoundError(
                resolver_name=self.name,
                track=track
            ) from exception
        except Exception as exception:
            raise ResolverError(
                (
                    f"Resolver {self.name!r} failed to extract a stream for "
                    f"track {track.title!r}."
                ),
                resolver_name=self.name
            ) from exception

        stream_url: str | None = self._extract_stream_url(information)

        if stream_url is None:
            raise StreamNotFoundError(
                resolver_name=self.name,
                track=track
            )

        return PlayableSource(
            stream_url=stream_url,
            source=MediaSource.YOUTUBE,
            headers=self._extract_headers(information),
            expires_at=self._extract_expiration(stream_url),
            seekable=not track.is_live
        )

    def _extract_information(self, track_url: str) -> dict[str, object]:
        """Extract and sanitize stream information with yt-dlp.

        Args:
            track_url:
                The public YouTube URL whose stream should be extracted.

        Returns:
            The sanitized yt-dlp information dictionary.

        Raises:
            DownloadError:
                yt-dlp could not extract the supplied YouTube URL.
            TypeError:
                yt-dlp returned an unexpected information value.
        """

        with YoutubeDL(dict(self._extractor_options)) as extractor:
            raw_information: object = extractor.extract_info(
                track_url,
                download=False
            )

            sanitized_information: object = extractor.sanitize_info(raw_information)

        if not isinstance(sanitized_information, dict):
            raise TypeError("yt-dlp returned an unexpected stream information value.")

        return cast(dict[str, object], sanitized_information)

    @staticmethod
    def _extract_stream_url(information: Mapping[str, object]) -> str | None:
        """Extract and validate the direct stream URL.

        Args:
            information:
                The sanitized yt-dlp information dictionary.

        Returns:
            The normalized direct stream URL, or ``None`` when unavailable.
        """

        raw_stream_url: object = information.get("url")

        if not isinstance(raw_stream_url, str):
            return None

        normalized_stream_url: str = raw_stream_url.strip()

        if not normalized_stream_url:
            return None

        try:
            parsed_stream_url = urlsplit(normalized_stream_url)
        except ValueError:
            return None

        if parsed_stream_url.scheme.casefold() not in {"http", "https"}:
            return None

        if parsed_stream_url.hostname is None:
            return None

        return normalized_stream_url

    @staticmethod
    def _extract_headers(information: Mapping[str, object]) -> dict[str, object]:
        """Extract normalized HTTP headers from stream information.

        Args:
            information:
                The sanitized yt-dlp information dictionary.

        Returns:
            Every valid HTTP header required to access the stream.
        """

        raw_hreaders: object = information.get("http_headers")

        if not isinstance(raw_hreaders, Mapping):
            return {}

        headers: dict[str, str] = {}

        for raw_header_name, raw_header_value in raw_hreaders.items():
            if not isinstance(raw_header_name, str):
                continue

            if not isinstance(raw_header_value, str):
                continue

            header_name: str = raw_header_name.strip()
            header_value: str = raw_header_value.strip()

            if header_name:
                headers[header_name] = header_value

        return headers

    @classmethod
    def _extract_expiration(cls, stream_url: str) -> datetime | None:
        """Extract an expiration timestamp from the stream URL.

        Args:
            stream_url:
                The direct stream URL returned by yt-dlp.

        Returns:
            The timezone-aware expiration timestamp, or ``None`` when the URL
            does not expose a valid expiration value.
        """

        try:
            query_parameters: dict[str, list[str]] = parse_qs(urlsplit(stream_url).query)
        except ValueError:
            return None

        for parameter_name in cls._EXPIRATION_PARAMETERS:
            for parameter_value in query_parameters.get(parameter_name, []):
                try:
                    expiration_timestamp: float = float(parameter_value)
                    expiration: datetime = datetime.fromtimestamp(
                        expiration_timestamp,
                        tz=UTC
                    )
                except (OSError, OverflowError, ValueError):
                    continue

                if expiration_timestamp > 0.0:
                    return expiration

        return None

    async def _close(self) -> None:
        """Release resolver-specific resources."""

        return None

__all__: tuple[str, ...] = ("YouTubeResolver",)
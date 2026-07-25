"""Direct HTTP metadata provider used by WumpiWave.

This module converts direct HTTP and HTTPS media URLs into normalized
WumpiWave tracks without performing a network request.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from hashlib import sha256
from urllib.parse import SplitResult, unquote, urlsplit, urlunsplit

from ..exceptions import UnsupportedQueryError
from ..models import (
    MediaQuery,
    MediaResult,
    MediaSource,
    MediaTrack,
    QueryType,
)
from .base import BaseMediaProvider

class HTTPProvider(BaseMediaProvider):
    """Convert direct HTTP media URLs into normalized media tracks.

    The provider performs URL validation and derives basic track metadata from
    the supplied URL. It does not verify whether the remote resource exists or
    contains playable audio.

    Attributes:
        name:
            The public provider name.
        source:
            The HTTP media source handled by the provider.
        closed:
            Whether the provider has released its resources.

    Methods:
        supports:
            Determine whether the provider supports a media query.
        query:
            Convert a direct HTTP URL into a media result.
        _normalize_url:
            Normalize and validate an HTTP or HTTPS URL.
        _create_identifier:
            Create a stable identifier for a normalized URL.
        _extract_title:
            Derive a readable track title from a normalized URL.
        _close:
            Release provider-specific resources.
    """

    __slots__ = ()

    _SUPPORTED_SCHEMES: frozenset[str] = frozenset(
        {
            "http",
            "https"
        }
    )

    def __init__(self) -> None:
        """Initialize a direct HTTP metadata provider."""

        super().__init__(
            name="http",
            source=MediaSource.HTTP
        )

    def supports(self, query: MediaQuery) -> bool:
        """Return whether the provider supports a media query.

        Args:
            query:
                The normalized media query to inspect.

        Returns:
            ``True`` when the query contains a valid direct HTTP or HTTPS URL.
        """

        if self.closed or query.query_type is not QueryType.URL:
            return False

        if query.source not in {
            None,
            MediaSource.HTTP,
            MediaSource.UNKNOWN
        }:
            return False

        return self._normalize_url(query.value) is not None

    async def query(self, query: MediaQuery) -> MediaResult:
        """Convert a direct HTTP URL into a media result.

        Args:
            query:
                The normalized direct URL query to process.

        Returns:
            A media result containing one normalized HTTP track.

        Raises:
            ProviderUnavailableError:
                The provider has already been closed.
            UnsupportedQueryError:
                The query does not contain a supported direct URL.
        """

        self._ensure_open()

        normalized_url: str | None = self._normalize_url(query.value)

        if not self.supports(query) or normalized_url is None:
            raise UnsupportedQueryError(query_value=query.value)

        track = MediaTrack(
            identifier=self._create_identifier(normalized_url),
            source=MediaSource.HTTP,
            title=self._extract_title(normalized_url),
            url=normalized_url
        )

        return MediaResult(
            query=query,
            source=MediaSource.HTTP,
            tracks=(track,)
        )

    @classmethod
    def _normalize_url(cls, value: str) -> str | None:
        """Normalize and validate an HTTP or HTTPS URL.

        URLs containing embedded authentication credentials are rejected.

        Args:
            value:
                The possible direct media URL.

        Returns:
            The normalized URL without a fragment, or ``None`` when invalid.
        """

        normalized_value: str = value.strip()

        if not normalized_value:
            return None

        try:
            parsed_url: SplitResult = urlsplit(normalized_value)
            parsed_url.port
        except ValueError:
            return None

        if parsed_url.scheme.casefold() not in cls._SUPPORTED_SCHEMES:
            return None

        if parsed_url.hostname is None:
            return None

        if parsed_url.username is not None or parsed_url.password is not None:
            return None

        if any(character.isspace() for character in parsed_url.netloc):
            return None

        return urlunsplit(
            (
                parsed_url.scheme.casefold(),
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.query,
                "",
            )
        )

    @staticmethod
    def _create_identifier(url: str) -> str:
        """Create a stable identifier for a normalized URL.

        Args:
            url:
                The normalized direct media URL.

        Returns:
            The hexadecimal SHA-256 digest of the URL.
        """

        return sha256(url.encode("utf-8")).hexdigest()

    @staticmethod
    def _extract_title(url: str) -> str:
        """Derive a readable track title from a normalized URL.

        Args:
            url:
                The normalized direct media URL.

        Returns:
            The final URL path component or hostname as a fallback.
        """

        parsed_url: SplitResult = urlsplit(url)
        path_segments: tuple[str, ...] = tuple(segment for segment in parsed_url.path.split("/") if segment)

        if path_segments:
            decoded_title: str = unquote(path_segments[-1]).strip()

            if decoded_title:
                return decoded_title
        return parsed_url.hostname or "HTTP stream"

    async def _close(self) -> None:
        """Release provider-specific resources."""

        return None

__all__: tuple[str, ...] = ("HTTPProvider",)
"""Media query matching utilities used throughout WumpiWave.

This module provides URL validation and source detection for raw media query
values without performing network requests.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from urllib.parse import SplitResult, urlsplit
from xml import dom

from ..models import MediaSource


class QueryMatcher:
    """Inspect raw query values and identify supported media sources.

    The matcher validates HTTP and HTTPS URLs and determines whether a URL
    belongs to YouTube, Spotify, or another directly accessible HTTP source.
    Plain search text and malformed URLs do not produce a media source.

    Attributes:
        None

    Methods:
        is_url:
            Determine whether a value is a valid HTTP or HTTPS URL.
        detect_source:
            Detect the media source associated with a URL.
        matches_source:
            Determine whether a URL belongs to a specific media source.
        _split_url:
            Parse and validate a possible HTTP or HTTPS URL.
        _matches_domain:
            Determine whether a hostname belongs to a supported domain.
    """

    __slots__ = ()

    _SUPPORTED_SCHEMES: frozenset[str] = frozenset(
        [
            "http",
            "https"
        ]
    )
    _YOUTUBE_DOMAINS: tuple[str, ...] = (
        "youtube.com",
        "youtube-nocookie.com",
        "youtu.be"
    )
    _SPOTIFY_DOMAINS: tuple[str, ...] = ("spotify.com",)

    @classmethod
    def is_url(cls, value: str) -> bool:
        """Return whether a value is a valid HTTP or HTTPS URL.

        Args:
            value:
                The raw query value to inspect.

        Returns:
            ``True`` when the value contains a supported URL, otherwise
            ``False``.
        """

        return cls._split_url(value) is not None

    @classmethod
    def detect_source(cls, value: str) -> MediaSource | None:
        """Detect the media source associated with a URL.

        YouTube and Spotify URLs return their respective source. Other valid
        HTTP and HTTPS URLs are classified as direct HTTP media sources.

        Args:
            value:
                The raw URL or search value to inspect.

        Returns:
            The detected media source, or ``None`` when the value is not a
            valid HTTP or HTTPS URL.
        """

        parsed_url: SplitResult |None = cls._split_url(value)

        if parsed_url is None:
            return None

        hostname: str = parsed_url.hostname or ""

        if any(
            cls._matches_domain(hostname, domain)
            for domain in cls._YOUTUBE_DOMAINS
        ):
            return MediaSource.YOUTUBE

        if any(
            cls._matches_domain(hostname, domain)
            for domain in cls._SPOTIFY_DOMAINS
        ):
            return MediaSource.SPOTIFY

        return MediaSource.HTTP

    @classmethod
    def matches_source(cls, value: str, source: MediaSource) -> bool:
        """Return whether a URL belongs to a specific media source.

        Args:
            value:
                The raw URL or search value to inspect.
            source:
                The media source expected for the supplied value.

        Returns:
            ``True`` when the detected source matches the expected source,
            otherwise ``False``.
        """

        return cls.detect_source(value) is source

    @classmethod
    def _split_url(cls, value: str) -> SplitResult | None:
        """Parse and validate a possible HTTP or HTTPS URL.

        Args:
            value:
                The raw query value to parse.

        Returns:
            The parsed URL when valid, otherwise ``None``.
        """

        normalized_value: str = value.strip()

        if not normalized_value:
            return None

        try:
            parsed_url: SplitResult = urlsplit(normalized_value)
            hostname: str | None = parsed_url.hostname
        except ValueError:
            return None

        if parsed_url.scheme.casefold() not in cls._SUPPORTED_SCHEMES:
            return None

        if hostname is None or not hostname.strip():
            return None

        if any(character.isspace() for character in parsed_url.netloc):
            return None

        return parsed_url

    @staticmethod
    def _matches_domain(hostname: str, domain: str) -> bool:
        """Return whether a hostname belongs to a domain.

        Args:
            hostname:
                The normalized hostname extracted from a URL.
            domain:
                The root domain to compare against.

        Returns:
            ``True`` when the hostname equals the domain or one of its
            subdomains, otherwise ``False``.
        """

        normalized_hostname: str = hostname.casefold().rstrip(".")
        normalized_domain: str = domain.casefold().rstrip(".")

        return (
            normalized_hostname == normalized_domain
            or normalized_hostname.endswith(f".{normalized_domain}")
        )

__all__: tuple[str, ...] = ("QueryMatcher",)
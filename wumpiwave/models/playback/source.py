"""
Playable source models used throughout WumpiWave.

This module provides the source-independent representation of temporary audio
streams returned by stream resolvers and consumed by playback backends.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from ..enums import MediaSource
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType

@dataclass(frozen=True, slots=True)
class PlayableSource:
    """
    Represents a temporary audio stream ready for playback.

    A playable source contains the resolved stream URL and connection metadata
    required by a playback backend. It is intentionally separated from
    ``MediaTrack`` because stream URLs may expire or require temporary HTTP
    headers.

    Attributes:
        - stream_url:
            The direct URL of the resolved audio stream.
        - source:
            The platform or source from which the stream originates.
        - headers:
            The immutable HTTP headers required to access the stream.
        - expires_at:
            The UTC date and time at which the stream URL expires, when known.
        - seekable:
            Whether playback can begin at an arbitrary position in the stream.

    Methods:
        __post_init__:
            Normalizes and validates the stream URL, headers, and expiration.
        expired:
            Indicates whether the playable source has expired.
        remaining_lifetime:
            Returns the remaining stream lifetime in seconds.
    """

    stream_url: str
    source: MediaSource
    headers: Mapping[str, str] = field(default_factory=dict)
    expires_at: datetime | None = None
    seekable: bool = False

    def __post_init__(self) -> None:
        """
        Normalize and validate the playable source data.

        Raises:
            ValueError:
                The stream URL is empty, an HTTP header name is empty, or the
                expiration date does not contain timezone information.
        """

        normalized_stream_url: str = self.stream_url.strip()

        if not normalized_stream_url:
            raise ValueError("The stream URL cannot be empty.")

        normalized_headers: dict[str, str] = {}

        for header_name, header_value in self.headers.items():
            normalized_header_name: str = header_name.strip()

            if not normalized_header_name:
                raise ValueError("The header name cannot be empty.")

            normalized_headers[normalized_header_name] = header_value.strip()

        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise ValueError("The stream expiration date must contain timezone information.")

        object.__setattr__(self, "stream_url", normalized_stream_url)
        object.__setattr__(self, "headers", MappingProxyType(normalized_headers))

    @property
    def expired(self) -> bool:
        """
        Return whether the playable source has expired.

        Returns:
            ``True`` when the expiration date has passed, otherwise ``False``.
            Sources without an expiration date never report as expired.
        """

        if self.expires_at is None:
            return False

        return datetime.now(UTC) >= self.expires_at

    @property
    def remaining_lifetime(self) -> float | None:
        """
        Return the remaining stream lifetime in seconds.

        Returns:
            The number of seconds until expiration, ``0.0`` when already
            expired, or ``None`` when no expiration date is known.
        """

        if self.expires_at is None:
            return None

        remaining_seconds: float = (
            self.expires_at - datetime.now(UTC)
        ).total_seconds()

        return max(0.0, remaining_seconds)

__all__: tuple[str, ...] = (
    "PlayableSource",
)
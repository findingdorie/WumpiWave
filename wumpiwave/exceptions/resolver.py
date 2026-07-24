"""Resolver exceptions raised throughout WumpiWave.

This module defines errors related to resolver registration, resolver lookup,
unsupported media tracks, missing streams, and expired playable sources.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from ..models import MediaTrack, PlayableSource
from .base import WumpiWaveError


class ResolverError(WumpiWaveError):
    """Represents the base exception for stream resolver errors.

    Attributes:
        - resolver_name:
            The public name of the resolver associated with the error, when
            available.

    Methods:
        __init__.py:
            Initializes the exception with a message and optional resolver name.
    """

    __slots__ = ("resolver_name",)

    resolver_name: str | None

    def __init__(self, message: str, *, resolver_name: str | None = None) -> None:
        """Initialize a resolver error.

        Args:
            message:
                The human-readable error message.
            resolver_name:
                The public name of the resolver associated with the error,
                when available.
        """
        self.resolver_name = resolver_name
        super().__init__(message)


class ResolverAlreadyRegisteredError(ResolverError):
    """Represents an attempt to register an existing resolver name.

    Attributes:
        - resolver_name:
            The resolver name already registered with the media client.

    Methods:
        __init__.py:
            Initializes the exception with the duplicate resolver name.
    """

    __slots__ = ()

    def __init__(self, resolver_name: str) -> None:
        """Initialize a resolver-already-registered error.

        Args:
            resolver_name:
                The duplicate resolver name.
        """
        super().__init__(
            f"The stream resolver {resolver_name!r} is already registered.",
            resolver_name=resolver_name,
        )


class ResolverNotFoundError(ResolverError):
    """Represents a requested resolver that is not registered.

    Attributes:
        - resolver_name:
            The resolver name that could not be found.

    Methods:
        __init__.py:
            Initializes the exception with the missing resolver name.
    """

    __slots__ = ()

    def __init__(self, resolver_name: str) -> None:
        """Initialize a resolver-not-found error.

        Args:
            resolver_name:
                The resolver name that could not be found.
        """
        super().__init__(
            f"No stream resolver named {resolver_name!r} is registered.",
            resolver_name=resolver_name,
        )


class UnsupportedMediaError(ResolverError):
    """Represents a media track unsupported by every registered resolver.

    Attributes:
        - resolver_name:
            Always ``None`` because no compatible resolver was found.
        - track:
            The media track unsupported by the registered resolvers.

    Methods:
        __init__.py:
            Initializes the exception with the unsupported media track.
    """

    __slots__ = ("track",)

    track: MediaTrack

    def __init__(self, track: MediaTrack) -> None:
        """Initialize an unsupported-media error.

        Args:
            track:
                The media track unsupported by registered resolvers.
        """
        self.track = track
        super().__init__(
            f"No registered stream resolver supports track "
            f"{track.title!r} from source {track.source.value!r}."
        )


class StreamNotFoundError(ResolverError):
    """Represents a resolver that could not find a playable stream.

    Attributes:
        - resolver_name:
            The resolver that attempted to locate the stream.
        - track:
            The media track for which no stream was found.

    Methods:
        __init__.py:
            Initializes the exception with the resolver and media track.
    """

    __slots__ = ("track",)

    track: MediaTrack

    def __init__(self, resolver_name: str, track: MediaTrack) -> None:
        """Initialize a stream-not-found error.

        Args:
            resolver_name:
                The resolver that attempted to locate the stream.
            track:
                The media track for which no stream was found.
        """
        self.track = track
        super().__init__(
            (
                f"Resolver {resolver_name!r} could not find a playable stream "
                f"for track {track.title!r}."
            ),
            resolver_name=resolver_name,
        )


class StreamExpiredError(ResolverError):
    """Represents a playable source whose stream URL has expired.

    Attributes:
        - resolver_name:
            The resolver that originally produced the playable source, when
            available.
        - source:
            The playable source containing the expired stream URL.

    Methods:
        __init__.py:
            Initializes the exception with the expired playable source.
    """

    __slots__ = ("source",)

    source: PlayableSource

    def __init__(
        self, source: PlayableSource, *, resolver_name: str | None = None
    ) -> None:
        """Initialize a stream-expired error.

        Args:
            source:
                The playable source containing the expired stream URL.
            resolver_name:
                The resolver that originally produced the source, when
                available.
        """
        self.source = source
        super().__init__(
            f"The playable stream from source {source.source.value!r} has expired.",
            resolver_name=resolver_name,
        )


__all__: tuple[str, ...] = (
    "ResolverAlreadyRegisteredError",
    "ResolverError",
    "ResolverNotFoundError",
    "StreamExpiredError",
    "StreamNotFoundError",
    "UnsupportedMediaError",
)

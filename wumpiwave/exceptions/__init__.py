"""Public exceptions raised throughout WumpiWave.

This package contains the exception hierarchy shared by media queries,
providers, resolvers, playback queues, voice backends, and media players.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .backend import (
    BackendConnectionError,
    BackendError,
    BackendNotConnectedError,
    BackendPlaybackError,
    BackendUnavailableError,
)
from .base import WumpiWaveError
from .player import (
    InvalidPlayerStateError,
    NoCurrentTrackError,
    PlayerAlreadyExistsError,
    PlayerDestroyedError,
    PlayerError,
    PlayerNotFoundError,
)
from .provider import (
    ProviderAlreadyRegisteredError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderUnavailableError,
)
from .query import (
    InvalidQueryError,
    MediaNotFoundError,
    QueryError,
    UnsupportedQueryError,
)
from .queue import (
    QueueEmptyError,
    QueueEntryNotFoundError,
    QueueError,
    QueueIndexOutOfRangeError,
)
from .resolver import (
    ResolverAlreadyRegisteredError,
    ResolverError,
    ResolverNotFoundError,
    StreamExpiredError,
    StreamNotFoundError,
    UnsupportedMediaError,
)

__all__: tuple[str, ...] = (
    "BackendConnectionError",
    "BackendError",
    "BackendNotConnectedError",
    "BackendPlaybackError",
    "BackendUnavailableError",
    "InvalidPlayerStateError",
    "InvalidQueryError",
    "MediaNotFoundError",
    "NoCurrentTrackError",
    "PlayerAlreadyExistsError",
    "PlayerDestroyedError",
    "PlayerError",
    "PlayerNotFoundError",
    "ProviderAlreadyRegisteredError",
    "ProviderAuthenticationError",
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderRateLimitError",
    "ProviderRequestError",
    "ProviderUnavailableError",
    "QueryError",
    "QueueEmptyError",
    "QueueEntryNotFoundError",
    "QueueError",
    "QueueIndexOutOfRangeError",
    "ResolverAlreadyRegisteredError",
    "ResolverError",
    "ResolverNotFoundError",
    "StreamExpiredError",
    "StreamNotFoundError",
    "UnsupportedMediaError",
    "UnsupportedQueryError",
    "WumpiWaveError",
)
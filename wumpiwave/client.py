"""High-level WumpiWave client implementation.

This module coordinates metadata providers, stream resolvers, and media
players through one central asynchronous client.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from .events import PlaybackEventDispatcher
from .exceptions import WumpiWaveError
from .models import LoopMode, MediaQuery, MediaResult
from .playback import PlaybackQueue, PlayerRegistry, WumpiWavePlayer
from .protocols import EventDispatcher, PlaybackBackend
from .providers import ProviderRegistry
from .resolvers import ResolverRegistry

class WumpiWaveClient:
    """Coordinate WumpiWave providers, resolvers, and media players.

    The client owns central provider, resolver, and player registries. Metadata
    queries are routed through registered providers, while created players
    share the configured resolver registry.

    Closing the client destroys every registered player before closing stream
    resolvers and metadata providers.

    Attributes:
        providers:
            The registry containing available metadata providers.
        resolvers:
            The registry containing available stream resolvers.
        players:
            The registry containing active media players.
        closed:
            Whether the client has released its resources.

    Methods:
        query:
            Route a normalized media query to a metadata provider.
        create_player:
            Create and register a media player.
        get_player:
            Return a registered player by identifier.
        destroy_player:
            Destroy and unregister one media player.
        close:
            Destroy players and close all owned registries.
        __aenter__:
            Enter the asynchronous client context.
        __aexit__:
            Leave the asynchronous client context and close the client.
        _ensure_open:
            Ensure that the client has not been closed.
    """

    __slots__ = (
        "_closed",
        "_players",
        "_providers",
        "_resolvers"
    )

    _closed: bool
    _players: PlayerRegistry
    _providers: ProviderRegistry
    _resolvers: ResolverRegistry

    def __init__(
            self,
            *,
            providers: ProviderRegistry | None = None,
            resolvers: ResolverRegistry | None = None,
            players: PlayerRegistry | None = None
    ) -> None:
        """Initialize a WumpiWave client.

        Args:
            providers:
                An optional existing metadata provider registry.
            resolvers:
                An optional existing stream resolver registry.
            players:
                An optional existing media player registry.
        """

        self._providers = (ProviderRegistry() if providers is None else providers)
        self._resolvers = (ResolverRegistry() if resolvers is None else resolvers)
        self._players = PlayerRegistry() if players is None else players
        self._closed = False

    @property
    def providers(self) -> ProviderRegistry:
        """Return the metadata provider registry.

        Returns:
            The registry used to process media queries.
        """

        return self._providers

    @property
    def resolvers(self) -> ResolverRegistry:
        """Return the stream resolver registry.

        Returns:
            The registry used to create playable media sources.
        """

        return self._resolvers

    @property
    def players(self) -> PlayerRegistry:
        """Return the media player registry.

        Returns:
            The registry containing active media players.
        """

        return self._players

    @property
    def closed(self) -> bool:
        """Return whether the client has been closed.

        Returns:
            ``True`` when the client can no longer be used.
        """

        return self._closed

    async def query(self, query: MediaQuery) -> MediaResult:
        """Route a normalized media query to a metadata provider.

        Args:
            query:
                The normalized media query to process.

        Returns:
            The media result returned by the selected provider.

        Raises:
            WumpiWaveError:
                The client has already been closed.
            UnsupportedQueryError:
                No registered provider supports the query.
            ProviderError:
                The selected provider could not process the query.
        """

        self._ensure_open()
        return await self._providers.query(query)

    def create_player(
            self,
            identifier: int,
            backend: PlaybackBackend,
            *,
            dispatcher: EventDispatcher,
            queue: PlaybackQueue | None = None,
            loop_mode: LoopMode = LoopMode.OFF,
            volume: float = 1.0,
            history_limit: int = 100
    ) -> WumpiWavePlayer:
        """Create and register a media player.

        The created player shares the client's resolver registry. Destroying
        an individual player therefore does not close the shared resolvers.

        Args:
            identifier:
                The numeric identifier associated with the player.
            backend:
                The playback backend used to deliver resolved audio.
            dispatcher:
                An optional playback event dispatcher.
            queue:
                An optional existing playback queue.
            loop_mode:
                The initial playback loop mode.
            volume:
                The initial playback volume.
            history_limit:
                The maximum number of retained playback history entries.

        Returns:
            The newly created and registered media player.

        Raises:
            WumpiWaveError:
                The client has already been closed.
            PlayerAlreadyExistsError:
                A player already uses the supplied identifier.
            TypeError:
                The identifier or another argument has an invalid type.
            ValueError:
                The volume or history limit is invalid.
        """

        self._ensure_open()

        player = WumpiWavePlayer(
            identifier=identifier,
            backend=backend,
            resolvers=self._resolvers,
            dispatcher=dispatcher,
            queue=queue,
            loop_mode=loop_mode,
            volume=volume,
            history_limit=history_limit,
            close_resolvers=False,
        )
        self._players.register(player)

        return player

    def get_player(self, identifier: int) -> WumpiWavePlayer:
        """Return a registered media player.

        Args:
            identifier:
                The numeric identifier of the player.

        Returns:
            The matching registered WumpiWave player.

        Raises:
            WumpiWaveError:
                The client has already been closed.
            PlayerNotFoundError:
                No player uses the supplied identifier.
        """

        self._ensure_open()

        player = self._players.get(identifier)

        if not isinstance(player, WumpiWavePlayer):
            raise TypeError("The registered player is not a WumpiWavePlayer instance.")

        return player

    async def destroy_player(self, identifier: int) -> None:
        """Destroy and unregister one media player.

        Args:
            identifier:
                The numeric identifier of the player to destroy.

        Raises:
            WumpiWaveError:
                The client has already been closed.
            PlayerNotFoundError:
                No player uses the supplied identifier.
            Exception:
                Player-specific cleanup failed.
        """

        self._ensure_open()
        await self._players.destroy(identifier)

    async def close(self) -> None:
        """Destroy players and close all client registries.

        Every owned component receives a cleanup request even when another
        component fails. Calling this method more than once has no effect.

        Raises:
            ExceptionGroup:
                One or more client components failed during cleanup.
        """

        if self._closed:
            return

        self._closed = True
        exceptions: list[Exception] = []

        try:
            await self._players.destroy_all()
        except Exception as exception:
            exceptions.append(exception)

        try:
            await self._resolvers.close()
        except Exception as exception:
            exceptions.append(exception)

        try:
            await self._providers.close()
        except Exception as exception:
            exceptions.append(exception)

        if exceptions:
            raise ExceptionGroup(
                "One or more WumpiWave client resources failed to close.",
                exceptions
            )

    async def __aenter__(self) -> Self:
        """Enter the asynchronous client context.

        Returns:
            The active WumpiWave client.

        Raises:
            WumpiWaveError:
                The client has already been closed.
        """

        self._ensure_open()
        return self

    async def __aexit__(
            self,
            exception_type: type[BaseException] | None = None,
            exception: BaseException | None = None,
            traceback: TracebackType | None = None
    ) -> None:
        """Leave the asynchronous client context.

        Args:
            exception_type:
                The exception type raised inside the context, when present.
            exception:
                The exception raised inside the context, when present.
            traceback:
                The traceback associated with the exception, when present.
        """

        await self.close()

    def _ensure_open(self) -> None:
        """Ensure that the client has not been closed.

        Raises:
            WumpiWaveError:
                The client has already released its resources.
        """

        if self._closed:
            raise WumpiWaveError("The WumpiWave client has already been closed.")

__all__: tuple[str, ...] = ("WumpiWaveClient",)
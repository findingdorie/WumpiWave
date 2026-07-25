"""Discord voice playback backend used by WumpiWave.

This module connects WumpiWave playback sources to Discord voice channels
through discord.py and FFmpeg.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

import logging
from asyncio import (
    AbstractEventLoop,
    CancelledError,
    Task,
    get_running_loop,
)
from collections.abc import Coroutine
from multiprocessing.process import name
from typing import Any

from discord import (
    ClientException,
    StageChannel,
    VoiceChannel,
    VoiceClient,
)

from ..exceptions import (
    BackendConnectionError,
    BackendNotConnectedError,
    BackendPlaybackError,
)
from ..models import PlayableSource
from ..protocols import PlaybackCompletionCallback
from .base import BasePlaybackBackend
from .ffmpeg import DiscordPCMSource, FFmpegAudioSourceFactory

_logger: logging.Logger = logging.getLogger(__name__)


class DiscordVoiceBackend(BasePlaybackBackend):
    """Deliver resolved media sources to a Discord voice connection.

    The backend establishes and manages a discord.py voice connection, creates
    FFmpeg PCM audio sources, forwards playback completion callbacks into the
    asyncio event loop, and provides pause, resume, stop, and volume controls.

    An existing voice client may be supplied when WumpiWave should reuse an
    established Discord voice connection. Otherwise, the backend creates and
    owns a connection through the configured voice channel.

    Attributes:
        name:
            The normalized public backend name.
        closed:
            Whether the backend has released its resources.
        connected:
            Whether the Discord voice client is connected.
        playing:
            Whether Discord is currently playing audio.
        paused:
            Whether Discord playback is currently paused.
        volume:
            The current normalized playback volume.
        channel:
            The Discord voice or stage channel used by the backend.
        voice_client:
            The active Discord voice client, when connected.
        source_factory:
            The FFmpeg source factory used to create Discord audio sources.
        owns_voice_client:
            Whether the backend created and manages the voice client.

    Methods:
        connect:
            Connect the backend to its configured Discord voice channel.
        disconnect:
            Disconnect the active Discord voice client.
        move_to:
            Move the active voice connection to another channel.
        play:
            Begin playing a resolved source through Discord.
        pause:
            Pause active Discord audio playback.
        resume:
            Resume paused Discord audio playback.
        stop:
            Stop active Discord audio playback.
        set_volume:
            Change the active or default playback volume.
        _disconnect:
            Disconnect while optionally suppressing completion callbacks.
        _complete_playback:
            Finalize a completed Discord playback operation.
        _schedule_completion_callback:
            Schedule an asynchronous completion callback.
        _consume_callback_result:
            Consume and log completion callback failures.
        _require_voice_client:
            Return the connected Discord voice client.
        _close:
            Stop playback and disconnect during backend cleanup.
    """

    __slots__ = (
        "_audio_source",
        "_channel",
        "_connect_timeout",
        "_owns_voice_client",
        "_playback_generation",
        "_reconnect",
        "_source_factory",
        "_voice_client",
        "_volume"
    )

    _MAXIMUM_VOLUME: float = 2.0

    _audio_source: DiscordPCMSource | None
    _channel: VoiceChannel | StageChannel
    _connect_timeout: float
    _owns_voice_client: bool
    _playback_generation: int
    _reconnect: bool
    _source_factory: FFmpegAudioSourceFactory
    _voice_client: VoiceClient | None
    _volume: float

    def __init__(
            self,
            channel: VoiceChannel | StageChannel,
            *,
            voice_client: VoiceClient | None = None,
            source_factory: FFmpegAudioSourceFactory | None = None,
            connect_timeout: float = 30.0,
            reconnect: bool = True,
            volume: float = 1.0
    ) -> None:
        """Initialize a Discord voice playback backend.

        Args:
            channel:
                The Discord voice or stage channel used for the connection.
            voice_client:
                An optional existing Discord voice client.
            source_factory:
                The FFmpeg factory used to create Discord audio sources.
            connect_timeout:
                The maximum duration allowed for connection establishment.
            reconnect:
                Whether discord.py may reconnect during connection setup.
            volume:
                The initial playback volume between ``0.0`` and ``2.0``.

        Raises:
            TypeError:
                The supplied channel is not a voice or stage channel.
            ValueError:
                The timeout or initial volume is invalid.
        """

        if not isinstance(channel, VoiceChannel | StageChannel):
            raise TypeError("The Discord backend requires a voice or stage channel.")

        if connect_timeout <= 0.0:
            raise ValueError("The Discord voice connection timeout must be greater than zero.")

        normalized_volume: float = self._validate_discord_volume(volume)

        super().__slots__(name="discord")

        self._channel = channel
        self._voice_client = voice_client
        self._source_factory = source_factory or FFmpegAudioSourceFactory()
        self._connect_timeout = connect_timeout
        self._reconnect = reconnect
        self._volume = normalized_volume
        self._audio_source = None
        self._playback_generation = 0
        self._owns_voice_client = voice_client is None

    @property
    def channel(self) -> VoiceChannel | StageChannel:
        """Return the configured Discord voice channel.

        Returns:
            The voice or stage channel used by the backend.
        """

        return self._channel

    @property
    def voice_client(self) -> VoiceClient | None:
        """Return the active Discord voice client.

        Returns:
            The current voice client, or ``None`` when disconnected.
        """

        return self._voice_client

    @property
    def source_factory(self) -> FFmpegAudioSourceFactory:
        """Return the configured FFmpeg source factory.

        Returns:
            The factory used to create Discord audio sources.
        """

        return self._source_factory

    @property
    def owns_voice_client(self) -> bool:
        """Return whether the backend owns its Discord voice client.

        Returns:
            ``True`` when the backend created the connection.
        """

        return self._owns_voice_client

    @property
    def connected(self) -> bool:
        """Return whether the Discord voice client is connected.

        Returns:
            ``True`` when an active Discord voice connection exists.
        """

        return (
            self._voice_client is not None
            and self._voice_client.is_connected()
        )

    @property
    def playing(self) -> bool:
        """Return whether Discord is actively playing audio.

        Returns:
            ``True`` when an audio source is currently playing.
        """

        return (
            self._voice_client is not None
            and self._voice_client.is_playing()
        )

    @property
    def paused(self) -> bool:
        """Return whether Discord playback is paused.

        Returns:
            ``True`` when the active audio source is paused.
        """

        return (
            self._voice_client is not None
            and self._voice_client.is_paused()
        )

    @property
    def volume(self) -> float:
        """Return the current playback volume.

        Returns:
            The configured volume between ``0.0`` and ``2.0``.
        """

        return self._volume

    async def connect(self) -> None:
        """Connect the backend to its Discord voice channel.

        An existing connected voice client is reused. A disconnected external
        client is replaced with a newly created backend-owned connection.

        Raises:
            BackendConnectionError:
                Discord could not establish the voice connection.
            BackendError:
                The backend has already been closed.
        """

        self._ensure_open()

        if self.connected:
            return

        self._voice_client = None

        try:
            connected_client = await self._channel.connect(
                timeout=self._connect_timeout,
                reconnect=self._reconnect
            )
        except Exception as exception:
            raise BackendConnectionError(
                backend_name=self.name,
                reason=str(exception) or exception.__class__.__name__,
            ) from exception

        if not isinstance(connected_client, VoiceClient):
            try:
                await connected_client.disconnect(force=True)
            except Exception:
                pass

            raise BackendConnectionError(
                backend_name=self.name,
                reason="Discord returned an unsupported voice protocol implementation."
            )

        self._voice_client = connected_client
        self._owns_voice_client = True

    async def disconnect(self) -> None:
        """Disconnect the active Discord voice client.

        Disconnecting an already disconnected backend has no effect.

        Raises:
            BackendConnectionError:
                Discord could not close the voice connection.
            BackendError:
                The backend has already been closed.
        """

        self._ensure_open()
        await self._disconnect(suppress_completion=True)

    async def move_to(self, channel: VoiceChannel | StageChannel) -> None:
        """Move the active Discord connection to another channel.

        Args:
            channel:
                The destination Discord voice or stage channel.

        Raises:
            BackendNotConnectedError:
                The backend has no active Discord voice connection.
            BackendConnectionError:
                Discord could not move the voice connection.
            BackendError:
                The backend has already been closed.
            TypeError:
                The supplied destination is not a supported channel.
        """

        self._ensure_open()

        if not isinstance(channel, VoiceChannel | StageChannel):
            raise TypeError("The Discord backend requires a voice or stage channel.")

        voice_client: VoiceClient = self._require_voice_client()

        try:
            await voice_client.move_to(channel)
        except Exception as exception:
            raise BackendConnectionError(
                backend_name=self.name,
                reason=str(exception) or exception.__class__.__name__,
            ) from exception

        self._channel = channel

    async def play(
        self,
        source: PlayableSource,
        *,
        start_position: float = 0.0,
        volume: float = 1.0,
        on_complete: PlaybackCompletionCallback | None = None,
    ) -> None:
        """Begin playing a resolved media source through Discord.

        Args:
            source:
                The resolved playable media source.
            start_position:
                The initial playback position in seconds.
            volume:
                The playback volume between ``0.0`` and ``2.0``.
            on_complete:
                The optional asynchronous callback invoked after playback.

        Raises:
            BackendNotConnectedError:
                The backend has no active Discord voice connection.
            BackendPlaybackError:
                The source is expired, not seekable, already playing, or FFmpeg
                could not start playback.
            BackendError:
                The backend has already been closed.
            ValueError:
                The start position or volume is invalid.
        """

        self._ensure_open()

        voice_client: VoiceClient = self._require_voice_client()
        normalized_start_position: float = self._validate_start_position(start_position)
        normalized_volume: float = self._validate_volume(volume)

        if source.expired:
            raise BackendPlaybackError(
                backend_name=self.name,
                reason="The resolved media source has already expired.",
                operation="play"
            )

        if voice_client.is_playing() or voice_client.is_paused():
            raise BackendPlaybackError(
                backend_name=self.name,
                reason="The Discord voice client is already playing audio.",
                operation="play"
            )

        try:
            audio_source: DiscordPCMSource = self._source_factory.create(
                source,
                start_position=normalized_start_position,
                volume=normalized_volume
            )
        except Exception as exception:
            raise BackendPlaybackError(
                backend_name=self.name,
                reason=str(exception) or exception.__class__.__name__,
                operation="play"
            ) from exception

        event_loop: AbstractEventLoop = get_running_loop()
        self._playback_generation += 1
        playback_generation: int = self._playback_generation
        self._audio_source = audio_source
        self._volume = normalized_volume

        def after_playback(error: Exception | None) -> None:
            """Forward Discord playback completion to the event loop."""

            event_loop.call_soon_threadsafe(
                self._complete_playback,
                playback_generation,
                audio_source,
                on_complete,
                error
            )

            try:
                voice_client.play(
                    audio_source,
                    after=after_playback,
                )
            except Exception as exception:
                if self._audio_source is audio_source:
                    self._audio_source = None

                audio_source.cleanup()

                raise BackendPlaybackError(
                    backend_name=self.name,
                    reason=str(exception) or exception.__class__.__name__,
                    operation="play"
                ) from exception

    async def resume(self) -> None:
        """Resume paused Discord audio playback.

        Raises:
            BackendNotConnectedError:
                The backend has no active Discord voice connection.
            BackendPlaybackError:
                No paused playback operation can be resumed.
            BackendError:
                The backend has already been closed.
        """

        self._ensure_open()

        voice_client: VoiceClient = self._require_voice_client()

        if not voice_client.is_paused():
            raise BackendPlaybackError(
                backend_name=self.name,
                reason="No paused Discord playback can be resumed.",
                operation="resume"
            )

        voice_client.resume()

    async def stop(self) -> None:
        """Stop active Discord audio playback.

        Stopping an idle Discord voice client has no effect.

        Raises:
            BackendNotConnectedError:
                The backend has no active Discord voice connection.
            BackendError:
                The backend has already been closed.
        """

        self._ensure_open()

        voice_client: VoiceClient = self._require_voice_client()

        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

    async def set_volume(self, volume: float) -> None:
        """Change the active or default Discord playback volume.

        Args:
            volume:
                The new volume between ``0.0`` and ``2.0``.

        Raises:
            BackendError:
                The backend has already been closed.
            ValueError:
                The supplied volume is outside the supported range.
        """

        self._ensure_open()

        normalized_volume: float = self._validate_discord_volume(volume)
        self._volume = normalized_volume

        if self._audio_source is not None:
            self._audio_source.volume = normalized_volume

    async def _disconnect(self, *, suppress_completion: bool) -> None:
        """Disconnect the active Discord voice client.

        Args:
            suppress_completion:
                Whether pending playback completion callbacks should be ignored.

        Raises:
            BackendConnectionError:
                Discord could not close the active voice connection.
        """

        voice_client: VoiceClient | None = self._voice_client

        if voice_client is None:
            return

        if suppress_completion:
            self._playback_generation += 1

        audio_source: DiscordPCMSource | None = self._audio_source
        self._audio_source = None
        self._voice_client = None

        try:
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()

            if voice_client.is_connected():
                await voice_client.disconnect(force=True)
        except Exception as exception:
            raise BackendConnectionError(
                backend_name=self.name,
                reason=str(exception) or exception.__class__.__name__
            ) from exception
        finally:
            if audio_source is not None:
                audio_source.cleanup()

    def _complete_playback(
            self,
            playback_generation: int,
            audio_source: DiscordPCMSource,
            on_complete: PlaybackCompletionCallback | None,
            error: Exception | None
    ) -> None:
        """Finalize a completed Discord playback operation.

        Args:
            playback_generation:
                The generation identifying the completed playback operation.
            audio_source:
                The Discord audio source that completed.
            on_complete:
                The optional asynchronous completion callback.
            error:
                The playback error supplied by discord.py, when present.
        """

        audio_source.cleanup()

        if playback_generation != self._playback_generation:
            return

        if self._audio_source is audio_source:
            self._audio_source = None

        if on_complete is not None:
            self._schedule_completion_callback(
                on_complete,
                error
            )

    @staticmethod
    def _schedule_completion_callback(callback: PlaybackCompletionCallback, error: Exception | None) -> None:
        """Schedule an asynchronous playback completion callback.

        Args:
            callback:
                The asynchronous callback to execute.
            error:
                The Discord playback error, when present.
        """

        callback_result: Coroutine[Any, Any, None] = callback(error)
        callback_task: Task[None] = get_running_loop().create_task(
            callback_result
        )
        callback_task.add_done_callback(DiscordVoiceBackend._consume_callback_result)

    @staticmethod
    def _consume_callback_result(callback_task: Task[None]) -> None:
        """Consume and log a completion callback result.

        Args:
            callback_task:
                The completed asynchronous callback task.
        """

        try:
            callback_task.result()
        except CancelledError:
            return
        except Exception:
            _logger.exception("A Discord playback completion callback failed.")

    def _require_voice_client(self) -> VoiceClient:
        """Return the connected Discord voice client.

        Returns:
            The active connected Discord voice client.

        Raises:
            BackendNotConnectedError:
                No connected Discord voice client is available.
        """

        if self._voice_client is None or not self._voice_client.is_connected():
            raise BackendNotConnectedError(backend_name=self.name)

        return self._voice_client

    @classmethod
    def _validate_discord_volume(cls, volume: float) -> float:
        """Validate a Discord playback volume.

        Args:
            volume:
                The playback volume to validate.

        Returns:
            The validated volume as a float.

        Raises:
            ValueError:
                The volume is greater than ``2.0`` or otherwise invalid.
        """

        normalized_volume: float = cls._validate_volume(volume)

        if normalized_volume > cls._MAXIMUM_VOLUME:
            raise ValueError("The Discord playback volume must be between 0.0 and 2.0")

        return normalized_volume

    async def _close(self) -> None:
        """Stop playback and disconnect during backend cleanup."""

        await self._disconnect(suppress_completion=True)

__all__: tuple[str, ...] = ("DiscordVoiceBackend",)




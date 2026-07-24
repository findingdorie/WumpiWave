"""YouTube metadata provider used by WumpiWave.

This module provides metadata queries for YouTube videos, playlists, and
text-based searches using the YouTube Data API.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import partial
from urllib.parse import parse_qs, urlsplit

from ...exceptions import MediaNotFoundError, UnsupportedQueryError
from ...models import (
    MediaQuery,
    MediaResult,
    MediaSource,
    MediaTrack,
    QueryType,
)
from ...query import QueryMatcher
from ..base import BaseMediaProvider
from .client import YouTubeClient
from .parser import YouTubeParser


class YouTubeProvider(BaseMediaProvider):
    """Retrieve and normalize metadata from YouTube.

    The provider supports YouTube video URLs, playlist URLs, and text-based
    searches. Search and playlist responses are paginated automatically until
    the requested result limit is reached.

    Video metadata is loaded in batches and converted into WumpiWave's public
    media models through the YouTube parser.

    Attributes:
        name:
            The public provider name.
        source:
            The YouTube media source handled by the provider.
        closed:
            Whether the provider has released its resources.
        client:
            The asynchronous YouTube Data API client used by the provider.
        owns_client:
            Whether the provider owns and closes its YouTube client.

    Methods:
        supports:
            Determine whether the provider supports a media query.
        query:
            Process a YouTube URL or search query.
        _query_search:
            Process a text-based YouTube search.
        _query_video:
            Retrieve one YouTube video by its identifier.
        _query_playlist:
            Retrieve a YouTube playlist and its tracks.
        _collect_search_identifiers:
            Collect video identifiers from paginated search results.
        _collect_playlist_identifiers:
            Collect video identifiers from paginated playlist items.
        _load_tracks:
            Retrieve and normalize videos in API-sized batches.
        _extract_url_identifiers:
            Extract video and playlist identifiers from a YouTube URL.
        _first_query_value:
            Return the first usable value of a URL query parameter.
        _normalize_identifier:
            Normalize an optional YouTube resource identifier.
        _close:
            Close the internally owned YouTube client.
    """

    __slots__ = (
        "_client",
        "_owns_client"
    )

    _MAXIMUM_PAGE_SIZE: int = 50
    _VIDEO_PATH_PREFIXES: frozenset[str] = frozenset(
        {
            "embed",
            "live",
            "shorts",
            "v"
        }
    )

    _client: YouTubeClient
    _owns_client: bool

    def __init__(self, *, api_key: str | None = None, client: YouTubeClient | None = None) -> None:
        """Initialize a YouTube metadata provider.

        Exactly one of ``api_key`` or ``client`` must be supplied. A client
        created from an API key is owned and closed by the provider. An
        externally supplied client remains managed by its caller.

        Args:
            api_key:
                The API key used to create an internal YouTube client.
            client:
                An optional externally managed YouTube client.

        Raises:
            ValueError:
                Neither or both client configuration options were supplied.
        """

        if api_key is None and client is None:
            raise ValueError("A YouTube API key or an existing YouTube client is required.")

        if api_key is not None and client is not None:
            raise ValueError("A YouTube API key and an existing client cannot both be supplied.")

        super().__init__(
            name="youtube",
            source=MediaSource.YOUTUBE
        )

        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            self._client = YouTubeClient(api_key=api_key or "")
            self._owns_client = True

    @property
    def client(self) -> YouTubeClient:
        """Return the YouTube Data API client.

        Returns:
            The client used to perform YouTube metadata requests.
        """

        return self._client

    @property
    def owns_client(self) -> bool:
        """Return whether the provider owns its YouTube client.

        Returns:
            ``True`` when the provider created and manages the client.
        """

        return self._owns_client

    def supports(self, query: MediaQuery) -> bool:
        """Return whether the provider supports a media query.

        Search queries are supported when their preferred source is YouTube,
        unknown, or unspecified. URL queries must point to a recognized YouTube
        video or playlist.

        Args:
            query:
                The normalized media query to inspect.

        Returns:
            ``True`` when the provider can process the query, otherwise
            ``False``.
        """

        if self.closed:
            return False

        if query.source not in {
            None,
            MediaSource.UNKNOWN,
            MediaSource.YOUTUBE
        }:
            return False

        if query.query_type is QueryType.SEARCH:
            return True

        if not QueryMatcher.matches_source(
            query.value,
            MediaSource.YOUTUBE
        ):
            return False

        video_identifier, playlist_identifier = self._extract_url_identifiers(query.value)

        if video_identifier is not None:
            return True

        return (
            query.include_collections
            and playlist_identifier is not None
        )

    async def query(self, query: MediaQuery) -> MediaResult:
        """Process a YouTube URL or search query.

        Args:
            query:
                The normalized media query to process.

        Returns:
            The normalized media result produced from YouTube metadata.

        Raises:
            ProviderUnavailableError:
                The provider has already been closed.
            UnsupportedQueryError:
                The query is not supported by the YouTube provider.
            MediaNotFoundError:
                YouTube returned no matching media.
            ProviderError:
                A YouTube Data API request failed.
        """

        self._ensure_open()

        if not self.supports(query):
            raise UnsupportedQueryError(query_value=query.value)

        if query.query_type is QueryType.SEARCH:
            return await self._query_search(query)

        video_identifier, playlist_identifier = self._extract_url_identifiers(query.value)

        if video_identifier is not None:
            return await self._query_video(
                query,
                video_identifier
            )

        raise UnsupportedQueryError(query_value=query.value)

    async def _query_search(self, query: MediaQuery) -> MediaResult:
        """Process a text-based YouTube search.

        Args:
            query:
                The normalized search query to process.

        Returns:
            The normalized tracks returned by YouTube.

        Raises:
            MediaNotFoundError:
                The search returned no available videos.
            ProviderError:
                A YouTube Data API request failed.
        """

        video_identifiers: tuple[str, ...] = (
            await self._collect_search_identifiers(query)
        )

        if not video_identifiers:
            raise MediaNotFoundError(query_value=query.value)

        tracks: tuple[MediaTrack, ...] = await self._load_tracks(
            video_identifiers,
            include_statistics=query.include_statistics
        )

        if not tracks:
            raise MediaNotFoundError(query_value=query.value)

        return MediaResult(
            query=query,
            source=MediaSource.YOUTUBE,
            tracks=tracks[: query.limit]
        )

    async def _query_video(self, *, query: MediaQuery, video_identifier: str) -> MediaResult:
        """Retrieve one YouTube video by its identifier.

        Args:
            query:
                The normalized URL query being processed.
            video_identifier:
                The unique identifier of the YouTube video.

        Returns:
            A media result containing the requested video.

        Raises:
            MediaNotFoundError:
                The requested video was not returned by YouTube.
            ProviderError:
                The YouTube Data API request failed.
        """

        tracks: tuple[MediaTrack, ...] = await self._load_tracks(
            (video_identifier,),
            include_statistics=query.include_statistics
        )

        if not tracks:
            raise MediaNotFoundError(query_value=query.value)

        return MediaResult(
            query=query,
            source=MediaSource.YOUTUBE,
            tracks=(tracks[0],)
        )

    async def _query_playlist(self, *, query: MediaQuery, playlist_identifier: str) -> MediaResult:
        """Retrieve a YouTube playlist and its tracks.

        Args:
            query:
                The normalized playlist URL query being processed.
            playlist_identifier:
                The unique identifier of the YouTube playlist.

        Returns:
            A media result containing the playlist and its available tracks.

        Raises:
            MediaNotFoundError:
                The requested playlist was not returned by YouTube.
            ProviderError:
                A YouTube Data API request failed.
        """

        playlist_response = await self._client.fetch_playlist((playlist_identifier,))
        playlist_payloads = playlist_response.get("items", [])

        if not playlist_payloads:
            raise MediaNotFoundError(query_value=query.value)

        video_identifiers: tuple[str, ...] = (
            await self._collect_playlist_identifiers(
                playlist_identifier=playlist_identifier,
                result_limit=query.limit
            )
        )
        tracks: tuple[MediaTrack, ...] = await self._load_tracks(
            video_identifiers,
            include_statistics=query.include_statistics
        )
        collection = YouTubeParser.parse_playlist(
            playlist_payloads[0],
            tracks=tracks
        )

        return MediaResult(
            query=query,
            source=MediaSource.YOUTUBE,
            tracks=tracks,
            collection=collection
        )

    async def _collect_search_identifiers(self, query: MediaQuery) -> tuple[str, ...]:
        """Collect video identifiers from paginated search results.

        Args:
            query:
                The normalized search query being processed.

        Returns:
            Unique video identifiers in their original search order.

        Raises:
            ProviderError:
                A YouTube Data API request failed.
        """

        identifiers: list[str] = []
        known_identifiers: set[str] = set()
        known_page_tokens: set[str] = set()
        page_token: str | None = None

        while len(identifiers) < query.limit:
            remaining_results: int = query.limit - len(identifiers)
            response = await self._client.search(
                query.value,
                result_limit=min(
                    remaining_results,
                    self._MAXIMUM_PAGE_SIZE
                ),
                resource_type="video",
                page_token=page_token
            )

            for identifier in YouTubeParser.extract_search_video_identifiers(response):
                if identifier in known_identifiers:
                    continue

                known_identifiers.add(identifier)
                identifiers.append(identifier)

                if len(identifiers) >= query.limit:
                    break

            next_page_token: str | None = self._normalize_identifier(response.get("nextPageToken"))

            if (
                next_page_token is None
                or next_page_token in known_page_tokens
            ):
                break

            known_page_tokens.add(next_page_token)
            page_token = next_page_token

        return tuple(identifiers)

    async def _collect_playlist_identifiers(self, *, playlist_identifier: str, result_limit: int) -> tuple[str, ...]:
        """Collect video identifiers from paginated playlist items.

        Args:
            playlist_identifier:
                The unique identifier of the YouTube playlist.
            result_limit:
                The maximum number of video identifiers to collect.

        Returns:
            Unique video identifiers in playlist order.

        Raises:
            ProviderError:
                A YouTube Data API request failed.
        """

        identifiers: list[str] = []
        known_identifiers: set[str] = set()
        known_page_tokens: set[str] = set()
        page_token: str | None = None

        while len(identifiers) < result_limit:
            remaining_results: int = result_limit - len(identifiers)
            response = await self._client.fetch_playlist_items(
                playlist_identifier,
                result_limit=min(
                    remaining_results,
                    self._MAXIMUM_PAGE_SIZE
                ),
                page_token=page_token
            )

            page_identifiers: tuple[str, ...] = (YouTubeParser.extract_playlist_video_identifiers((response,)))

            for identifier in page_identifiers:
                if identifier in known_identifiers:
                    continue

                known_identifiers.add(identifier)
                identifiers.append(identifier)

                if len(identifiers) >= result_limit:
                    break

            next_page_token: str | None = self._normalize_identifier(response.get("nextPageToken"))

            if (
                next_page_token is None
                or next_page_token in known_page_tokens
            ):
                break

            known_page_tokens.add(next_page_token)
            page_token = next_page_token

        return tuple(identifiers)

    async def _load_tracks(self, video_identifiers: Iterable[str], *, include_statistics: bool) -> tuple[MediaTrack, ...]:
        """Retrieve and normalize videos in API-sized batches.

        The final tracks retain the original identifier order even when the API
        returns video resources in a different order.

        Args:
            video_identifiers:
                The YouTube video identifiers to retrieve.
            include_statistics:
                Whether public video statistics should be requested.

        Returns:
            Every available media track in the requested identifier order.

        Raises:
            ProviderError:
                A YouTube Data API request failed.
        """

        normalized_identifiers: tuple[str, ...] = tuple(
            dict.fromkeys(
                identifier
                for identifier in (
                    self._normalize_identifier(value)
                    for value in video_identifiers
                )
                if identifier is not None
            )
        )

        if not normalized_identifiers:
            return ()

        tracks_by_identifier: dict[str, MediaTrack] = {}

        for batch_start in range(
            0,
            len(normalized_identifiers),
            self._MAXIMUM_PAGE_SIZE
        ):
            batch: tuple[str, ...] = normalized_identifiers[batch_start : batch_start + self._MAXIMUM_PAGE_SIZE]
            response = await self._client.fetch_videos(
                batch,
                include_statistics=include_statistics
            )

            for track in YouTubeParser.parse_videos(response.get("items", [])):
                tracks_by_identifier[track.identifier] = track

        return tuple(
            tracks_by_identifier[identifier]
            for identifier in normalized_identifiers
            if identifier in tracks_by_identifier
        )

    @classmethod
    def _extract_url_identifiers(cls, query_value: str) -> tuple[str | None, str | None]:
        """Extract video and playlist identifiers from a YouTube URL.

        Supported video forms include regular watch URLs, shortened URLs,
        Shorts, livestreams, embeds, and legacy ``/v/`` URLs.

        Args:
            query_value:
                The YouTube URL to inspect.

        Returns:
            The optional video and playlist identifiers.
        """

        try:
            parsed_url = urlsplit(query_value.strip())
            query_parameters: dict[str, list[str]] = parse_qs(parsed_url.query)
        except ValueError:
            return None, None

        hostname: str = (parsed_url.hostname or "").casefold().rstrip(".")
        path_parts: tuple[str, ...] = tuple(
            part
            for part in parsed_url.path.split("/")
            if part
        )
        playlist_identifier: str | None = cls._first_query_value(
            query_parameters,
            "list"
        )
        video_identifier: str | None = None

        if hostname == "youtu.be" or hostname.endswith(".youtu.be"):
            if path_parts:
                video_identifier = cls.normalize_identifier(path_parts[0])
        elif path_parts:
            first_path_part: str = path_parts[0].casefold()

            if first_path_part == "watch":
                video_identifier = cls._first_query_value(
                    query_parameters,
                    "v"
                )
            elif (
                first_path_part in cls._VIDEO_PATH_PREFIXES
                and len(path_parts) >= 2
            ):
                video_identifier = cls._normalize_identifier(path_parts[1])

        return video_identifier, playlist_identifier

    @classmethod
    def _first_query_value(cls, query_parameters: dict[str, list[str]], parameter_name: str) -> str | None:
        """Return the first usable value of a URL query parameter.

        Args:
            query_parameters:
                The parsed URL query parameters.
            parameter_name:
                The query parameter whose value should be returned.

        Returns:
            The first normalized parameter value, or ``None``.
        """

        for value in query_parameters.get(parameter_name, []):
            normalized_value: str | None = cls._normalize_identifier(value)

            if normalized_value is not None:
                return normalized_value

        return None

    @staticmethod
    def _normalize_identifier(identifier: str | None) -> str | None:
        """Normalize an optional YouTube resource identifier.

        Args:
            identifier:
                The optional identifier to normalize.

        Returns:
            The stripped identifier, or ``None`` when it is unavailable.
        """

        if identifier is None:
            return None

        normalized_identifier: str = identifier.strip()
        return normalized_identifier or None

    async def _close(self) -> None:
        """Close the internally owned YouTube client."""

        if self._owns_client:
            await self._client.close()

__all__: tuple[str, ...] = ("YouTubeProvider",)
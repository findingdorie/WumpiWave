"""Spotify metadata provider used by WumpiWave.

This module provides metadata queries for Spotify tracks, albums, playlists,
and text-based searches using the Spotify Web API.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from idlelib.debugobj_r import remote_object_tree_item
from typing import Literal
from urllib.parse import urlsplit

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
from .client import SpotifyClient
from .models import (
    _SpotifyAlbumPayload,
    _SpotifyPlaylistItemPagingPayload,
    _SpotifyPlaylistPayload,
    _SpotifySearchResponsePayload,
    _SpotifySimplifiedTrackPayload,
)
from .parser import SpotifyParser

type _SpotifyResourceType = Literal["album", "playlist", "track"]

class SpotifyProvider(BaseMediaProvider):
    """Retrieve and normalize metadata from Spotify.

    The provider supports Spotify track, album, and playlist URLs together
    with text-based track searches. Search and collection requests are
    paginated automatically until the requested number of playable tracks has
    been collected.

    Spotify only supplies metadata. Tracks returned by this provider require a
    separate stream resolver before they can be played.

    Attributes:
        name:
            The public provider name.
        source:
            The Spotify media source handled by the provider.
        closed:
            Whether the provider has released its resources.
        client:
            The asynchronous Spotify Web API client used by the provider.
        market:
            The optional ISO 3166-1 alpha-2 market used for catalog requests.
        owns_client:
            Whether the provider owns and closes its Spotify client.

    Methods:
        supports:
            Determine whether the provider supports a media query.
        query:
            Process a Spotify URL or text-based search query.
        _query_search:
            Process a text-based Spotify track search.
        _query_track:
            Retrieve one Spotify track.
        _query_album:
            Retrieve a Spotify album and its tracks.
        _query_playlist:
            Retrieve a Spotify playlist and its playable tracks.
        _collect_search_tracks:
            Collect tracks from paginated Spotify search responses.
        _collect_album_tracks:
            Collect tracks from a paginated Spotify album.
        _collect_playlist_tracks:
            Collect tracks from paginated Spotify playlist items.
        _extract_resource_reference:
            Extract a resource type and identifier from a Spotify URL.
        _normalize_identifier:
            Normalize an optional Spotify resource identifier.
        _normalize_market:
            Normalize and validate an optional Spotify market.
        _close:
            Close the internally owned Spotify client.
    """

    __slots__ = (
        "_client",
        "_market",
        "_owns_client"
    )

    _MAXIMUM_COLLECTION_PAGE_SIZE: int = 50
    _MAXIMUM_SEARCH_OFFSET: int = 1_000
    _MAXIMUM_SEARCH_PAGE_SIZE: int = 10
    _SUPPORTED_RESOURCE_TYPES: frozenset[str] = frozenset(
        {
            "album",
            "playlist",
            "track"
        }
    )

    _client: SpotifyClient
    _market: str | None
    _owns_client: bool

    def __init__(
            self,
            *,
            client_id: str | None = None,
            client_secret: str | None = None,
            access_token: str | None = None,
            client: SpotifyClient | None = None,
            market: str | None = None
    ) -> None:
        """Initialize a Spotify metadata provider.

        Supply an existing Spotify client or authentication values used to
        create an internal client. Externally supplied clients remain managed
        by their caller.

        Args:
            client_id:
                The Spotify application client identifier.
            client_secret:
                The Spotify application client secret.
            access_token:
                An optional externally managed Spotify bearer token.
            client:
                An optional externally managed Spotify API client.
            market:
                An optional ISO 3166-1 alpha-2 market code used for requests.

        Raises:
            ValueError:
                The client configuration or market is invalid.
        """

        supplied_authentication: bool = any(
            value is not None
            for value in (
                client_id,
                client_secret,
                access_token
            )
        )

        if client is not None and supplied_authentication:
            raise ValueError(
                "An existing Spotify client cannot be combined with "
                "authentication values."
            )

        if client is None:
            client = SpotifyClient(
                client_id=client_id,
                client_secret=client_secret,
                access_token=access_token
            )
            owns_client: bool = True
        else:
            owns_client = False

        super().__init__(
            name="spotify",
            source=MediaSource.SPOTIFY
        )

        self._client = client
        self._market = market
        self._owns_client = owns_client

    @property
    def client(self) -> SpotifyClient:
        """Return the Spotify Web API client.

        Returns:
            The client used to perform Spotify metadata requests.
        """

        return self._client

    @property
    def market(self) -> str | None:
        """Return the configured Spotify market.

        Returns:
            The uppercase market code, or ``None`` when no market is set.
        """

        return self._market

    @property
    def owns_client(self) -> bool:
        """Return whether the provider owns its Spotify client.

        Returns:
            ``True`` when the provider created and manages the client.
        """

        return self._owns_client

    def supports(self, query: MediaQuery) -> bool:
        """Return whether the provider supports a media query.

        Search queries are supported when their preferred source is Spotify,
        unknown, or unspecified. URL queries must reference a Spotify track,
        album, or playlist.

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
            MediaSource.SPOTIFY
        }:
            return False

        if query.query_type is QueryType.SEARCH:
            return True

        if not QueryMatcher.matches_source(
            query.value,
            MediaSource.SPOTIFY
        ):
            return False

        resource_type, resource_identifier = self._extract_resource_reference(query.value)

        if resource_type is None or resource_identifier is None:
            return False

        if resource_type == "track":
            return True

        return query.include_collections

    async def query(self, query: MediaQuery) -> MediaResult:
        """Process a Spotify URL or search query.

        Args:
            query:
                The normalized media query to process.

        Returns:
            The normalized media result produced from Spotify metadata.

        Raises:
            ProviderUnavailableError:
                The provider has already been closed.
            UnsupportedQueryError:
                The query is unsupported by the Spotify provider.
            MediaNotFoundError:
                Spotify returned no matching media.
            ProviderError:
                A Spotify Web API request failed.
        """

        self._ensure_open()

        if not self.supports(query):
            raise UnsupportedQueryError(query_value=query.value)

        if query.query_type in QueryType.SEARCH:
            return await self._query_search(query)

        resource_type, resource_identifier = self._extract_resource_reference(query.value)

        if resource_type is None or resource_identifier is None:
            raise UnsupportedQueryError(query_value=query.value)

        if resource_type == "track":
            return await self.query_track(
                query=query,
                track_identifier=resource_identifier
            )

        if resource_type == "album":
            return await self._query_album(
                query=query,
                album_identifier=resource_identifier
            )

        return await self._query_playlist(
            query=query,
            playlist_identifier=resource_identifier
        )

    async def _query_search(self, query: MediaQuery) -> MediaResult:
        """Process a text-based Spotify track search.

        Args:
            query:
                The normalized search query to process.

        Returns:
            The normalized Spotify tracks matching the search.

        Raises:
            MediaNotFoundError:
                Spotify returned no matching tracks.
            ProviderError:
                A Spotify Web API request failed.
        """

        tracks: tuple[MediaTrack, ...] = await self._collect_search_tracks(query)

        if not tracks:
            raise MediaNotFoundError(query_value=query.value)

        return MediaResult(
            query=query,
            source=MediaSource.SPOTIFY,
            tracks=tracks
        )

    async def _query_track(self, *, query: MediaQuery, track_identifier: str) -> MediaResult:
        """Retrieve one Spotify track.

        Args:
            query:
                The normalized track URL query.
            track_identifier:
                The unique Spotify track identifier.

        Returns:
            A media result containing the requested track.

        Raises:
            MediaNotFoundError:
                Spotify returned no usable track.
            ProviderError:
                A Spotify Web API request failed.
        """

        payload = await self._client.fetch_track(
            track_identifier,
            market=self.market
        )
        track: MediaTrack = SpotifyParser.parse_track(payload)

        return MediaResult(
            query=query,
            source=MediaSource.SPOTIFY,
            tracks=(track,)
        )

    async def _query_album(self, *, query: MediaQuery, album_identifier: str) -> MediaResult:
        """Retrieve a Spotify album and its tracks.

        Args:
            query:
                The normalized album URL query.
            album_identifier:
                The unique Spotify album identifier.

        Returns:
            A media result containing the album and its available tracks.

        Raises:
            MediaNotFoundError:
                Spotify returned no usable album metadata.
            ProviderError:
                A Spotify Web API request failed.
        """

        album_payload: _SpotifyAlbumPayload = await self._client.fetch_album(
            album_identifier,
            market=self.market
        )
        tracks: tuple[MediaTrack, ...] = await self._collect_album_tracks(
            album_payload=album_payload,
            result_limit=query.limit
        )
        collection = SpotifyParser.parse_album(
            album_payload,
            tracks=tracks
        )

        return MediaResult(
            query=query,
            source=MediaSource.SPOTIFY,
            tracks=tracks,
            collection=collection
        )

    async def _query_playlist(self, *, query: MediaQuery, playlist_identifier: str) -> MediaResult:
        """Retrieve a Spotify playlist and its playable tracks.

        Args:
            query:
                The normalized playlist URL query.
            playlist_identifier:
                The unique Spotify playlist identifier.

        Returns:
            A media result containing the playlist and available tracks.

        Raises:
            MediaNotFoundError:
                Spotify returned no usable playlist metadata.
            ProviderAuthenticationError:
                The configured token cannot access the playlist items.
            ProviderError:
                A Spotify Web API request failed.
        """

        playlist_payload: _SpotifyPlaylistPayload = (
            await self._client.fetch_playlist(
                playlist_identifier,
                market=self.market
            )
        )
        tracks: tuple[MediaTrack, ...] = await self._collect_playlist_tracks(
            playlist_identifier=playlist_identifier,
            result_limit=query.limit
        )
        collection = SpotifyParser.parse_playlist(
            playlist_payload,
            tracks=tracks
        )

        return MediaResult(
            query=query,
            source=MediaSource.SPOTIFY,
            tracks=tracks,
            collection=collection
        )

    async def _collect_search_tracks(self, query: MediaQuery) -> tuple[MediaTrack, ...]:
        """Collect tracks from paginated Spotify search responses.

        Args:
            query:
                The normalized Spotify search query.

        Returns:
            Unique matching tracks in their original search order.

        Raises:
            ProviderError:
                A Spotify Web API request failed.
        """

        tracks: list[MediaTrack] = []
        known_identifiers: set[str] = set()
        offset: int = 0

        while (
            len(tracks) < query.limit
            and offset <= self._MAXIMUM_SEARCH_OFFSET
        ):
            remaining_results: int = query.limit - len(tracks)
            page_limit: int = min(
                remaining_results,
                self._MAXIMUM_SEARCH_PAGE_SIZE
            )
            response: _SpotifySearchResponsePayload = (
                await self._client.search(
                    query.value,
                    resource_type="track",
                    result_limit=page_limit,
                    offset=offset,
                    market=self.market
                )
            )
            page_tracks: tuple[MediaTrack, ...] = (SpotifyParser.parse_search_tracks(response))

            if not page_tracks:
                break

            for track in page_tracks:
                if track.identifier in known_identifiers:
                    continue

                known_identifiers.add(track.identifier)
                tracks.append(track)

                if len(tracks) >= query.limit:
                    break

            track_page = response.get("tracks")

            if track_page is None:
                break

            returned_items: int = len(track_page.get("items", []))
            total_items: int = track_page.get("total", 0)

            if returned_items == 0:
                break

            offset += returned_items

            if offset >= total_items:
                break

        return tuple(tracks)

    async def _collect_album_tracks(self, *, album_payload: _SpotifyAlbumPayload, result_limit: int) -> tuple[MediaTrack, ...]:
        """Collect tracks from a paginated Spotify album.

        Args:
            album_payload:
                The complete Spotify album payload.
            result_limit:
                The maximum number of tracks to collect.

        Returns:
            The normalized album tracks in their original order.

        Raises:
            ProviderRequestError:
                The album payload contains invalid track metadata.
            ProviderError:
                A Spotify Web API request failed.
        """

        track_payloads: list[_SpotifySimplifiedTrackPayload] = []
        initial_page = album_payload.get("tracks")

        if initial_page is not None:
            track_payloads.extend(initial_page.get("items", []))

        track_payloads = track_payloads[:result_limit]
        offset: int = len(track_payloads)
        total_tracks: int = (
            initial_page.get("total", offset)
            if initial_page is not None
            else result_limit
        )

        while len(track_payloads) < result_limit and offset < total_tracks:
            remaining_results: int = result_limit - len(track_payloads)
            page = await self._client.fetch_album_tracks(
                album_payload["id"],
                result_limit=min(
                    remaining_results,
                    self._MAXIMUM_COLLECTION_PAGE_SIZE
                ),
                offset=offset,
                market=self.market
            )
            page_items: list[_SpotifySimplifiedTrackPayload] = page.get("items", [])

            if not page_items:
                break

            track_payloads.extend(page_items)
            next_offset: int = page.get("offset", offset) + len(page_items)

            if next_offset <= offset:
                break

            offset = next_offset
            total_tracks = page.get("total", total_tracks)

        return SpotifyParser.parse_album_tracks(
            track_payloads[:result_limit],
            album=album_payload
        )

    async def _collect_playlist_tracks(self, *, playlist_identifier: str, result_limit: int) -> tuple[MediaTrack, ...]:
        """Collect tracks from paginated Spotify playlist items.

        Local, null, and unsupported playlist items are ignored. Pagination
        continues until the requested number of playable tracks has been
        collected or no additional playlist items remain.

        Args:
            playlist_identifier:
                The unique Spotify playlist identifier.
            result_limit:
                The maximum number of playable tracks to collect.

        Returns:
            The normalized playable tracks in playlist order.

        Raises:
            ProviderAuthenticationError:
                The configured token cannot access the playlist items.
            ProviderError:
                A Spotify Web API request failed.
        """

        tracks: list[MediaTrack] = []
        offset: int = 0
        total_items: int | None = None

        while len(tracks) < result_limit:
            if total_items is not None and offset >= total_items:
                break

            remaining_results: int = result_limit - len(tracks)
            page: _SpotifyPlaylistItemPagingPayload = (
                await self._client.fetch_playlist_items(
                    playlist_identifier,
                    result_limit=min(
                        remaining_results,
                        self._MAXIMUM_COLLECTION_PAGE_SIZE
                    ),
                    offset=offset,
                    market=self.market
                )
            )
            page_items = page.get("items", [])

            if not page_items:
                break

            page_tracks: tuple[MediaTrack, ...] = (SpotifyParser.parse_playlist_items(page))
            tracks.extend(page_tracks[:remaining_results])

            next_offset: int = page.get("offset", offset) + len(page_tracks)

            if next_offset <= offset:
                break

            offset = next_offset
            total_items = page.get("total", total_items or 0)

        return tuple(tracks[:result_limit])

    @classmethod
    def _extract_resource_reference(cls, query_value: str) -> tuple[_SpotifyResourceType | None, str | None]:
        """Extract a resource type and identifier from a Spotify URL.

        Standard, localized, and embedded Spotify URLs are supported by
        scanning the URL path for a known resource type.

        Args:
            query_value:
                The Spotify URL to inspect.

        Returns:
            The optional Spotify resource type and identifier.
        """

        try:
            parsed_url = urlsplit(query_value.strip())
        except ValueError:
            return None, None

        path_parts: tuple[str, ...] = tuple(
            part.strip()
            for part in parsed_url.path.split("/")
            if part.strip()
        )

        for index, path_part in enumerate(path_parts[:-1]):
            normalized_resource_type: str = path_part.casefold()

            if normalized_resource_type not in cls._SUPPORTED_RESOURCE_TYPES:
                continue

            resource_identifier: str | None = cls._normalize_identifier(path_parts[index + 1])

            if resource_identifier is None:
                return None, None

            return (
                normalized_resource_type,
                resource_identifier,
            )

        return None, None

    @staticmethod
    def _normalize_identifier(identifier: str | None) -> str | None:
        """Normalize an optional Spotify resource identifier.

        Args:
            identifier:
                The optional identifier to normalize.

        Returns:
            The stripped identifier, or ``None`` when unavailable.
        """

        if identifier is None:
            return None

        normalized_identifier: str = identifier.strip()
        return normalized_identifier or None

    @staticmethod
    def _normalize_market(market: str | None) -> str | None:
        """Normalize and validate an optional Spotify market.

        Args:
            market:
                The optional ISO 3166-1 alpha-2 market code.

        Returns:
            The uppercase market code, or ``None`` when omitted.

        Raises:
            ValueError:
                The market is not a two-letter alphabetic code.
        """

        if market is None:
            return None

        normalized_market: str = market.strip().upper()

        if len(normalized_market) != 2 or not normalized_market.isalpha():
            raise ValueError("The Spotify market must be a two-letter alphabetic code.")

        return normalized_market

    async def _close(self) -> None:
        """Close the internally owned Spotify client."""

        if self._owns_client:
            await self._client.close()

__all__: tuple[str, ...] = ("SpotifyProvider",)
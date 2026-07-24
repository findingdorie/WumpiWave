"""Asynchronous Spotify Web API client used by WumpiWave.

This module provides authenticated request methods for retrieving tracks,
albums, playlists, playlist items, and Spotify search results.

Attributes:
    SpotifySearchResource:
        The Spotify resource types supported by catalog searches.

Methods:
    None
"""

from __future__ import annotations

from asyncio import Lock
from collections.abc import Iterable, Mapping
from http import HTTPStatus
from time import monotonic
from tokenize import endpats
from types import TracebackType
from typing import Literal, Self, cast

from aiohttp import BasicAuth, ClientError, ClientSession, ClientTimeout

from ...exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderUnavailableError,
)
from .models import (
    _SpotifyAccessTokenPayload,
    _SpotifyAlbumPayload,
    _SpotifyPlaylistItemPagingPayload,
    _SpotifyPlaylistPayload,
    _SpotifySearchResponsePayload,
    _SpotifySeveralTracksResponsePayload,
    _SpotifySimplifiedTrackPagingPayload,
    _SpotifyTokenErrorResponsePayload,
    _SpotifyTrackPayload,
)

type SpotifySearchResource = Literal["album", "playlist", "track"]

class SpotifyClient:
    """Provide asynchronous access to the Spotify Web API.

    The client supports automatic authentication through Spotify's client
    credentials flow or an externally supplied bearer token. Client
    credentials are suitable for catalog metadata that does not require access
    to a Spotify user account.

    An external bearer token can be used for endpoints requiring user
    authorization. The caller is responsible for refreshing externally
    supplied tokens.

    A client session may be supplied by the caller. Otherwise, the client
    creates and owns a session lazily when the first request is performed.

    Attributes:
        api_base_url:
            The normalized base URL used for Spotify Web API requests.
        accounts_base_url:
            The normalized base URL used for Spotify authentication requests.
        closed:
            Whether the client has been closed.
        owns_session:
            Whether the client owns and manages its HTTP session.
        request_timeout:
            The maximum duration of an individual request in seconds.
        uses_external_token:
            Whether authentication uses an externally supplied bearer token.

    Methods:
        fetch_track:
            Retrieve metadata for one Spotify track.
        fetch_tracks:
            Retrieve metadata for multiple Spotify tracks.
        fetch_album:
            Retrieve metadata for one Spotify album.
        fetch_album_tracks:
            Retrieve one page of tracks from a Spotify album.
        fetch_playlist:
            Retrieve metadata for one Spotify playlist.
        fetch_playlist_items:
            Retrieve one page of items from a Spotify playlist.
        search:
            Search Spotify for tracks, albums, or playlists.
        close:
            Close the internally owned HTTP session.
        __aenter__:
            Enter the asynchronous client context.
        __aexit__:
            Leave the asynchronous client context and close the client.
        _request:
            Perform an authenticated Spotify Web API request.
        _request_access_token:
            Request a client-credentials access token from Spotify Accounts.
        _get_access_token:
            Return a valid external or internally managed access token.
        _get_session:
            Return an active HTTP session.
        _raise_response_error:
            Convert an unsuccessful response into a WumpiWave exception.
        _extract_error_message:
            Extract an error description from a Spotify response.
        _normalize_identifier:
            Normalize and validate one Spotify resource identifier.
        _normalize_identifiers:
            Normalize and validate multiple Spotify resource identifiers.
        _normalize_market:
            Normalize and validate an optional Spotify market.
        _validate_pagination:
            Validate pagination parameters.
        _parse_retry_after:
            Parse an optional rate-limit retry delay.
        _ensure_open:
            Ensure that the client has not been closed.
    """

    __slots__ = (
        "_access_token",
        "_accounts_base_url",
        "_api_base_url",
        "_client_id",
        "_client_secret",
        "_closed",
        "_owns_session",
        "_request_timeout",
        "_session",
        "_token_expires_at",
        "_token_lock",
        "_uses_external_token",
    )

    _DEFAULT_ACCOUNTS_BASE_URL: str = "https://accounts.spotify.com"
    _DEFAULT_API_BASE_URL: str = "https://api.spotify.com/v1"
    _MAXIMUM_PAGE_SIZE: int = 50
    _MAXIMUM_SEARCH_LIMIT: int = 10
    _MAXIMUM_SEARCH_OFFSET: int = 1_000
    _MAXIMUM_TRACK_IDENTIFIERS: int = 50
    _PROVIDER_NAME: str = "spotify"
    _TOKEN_EXPIRATION_BUFFER: float = 30.0

    _access_token: str | None
    _accounts_base_url: str
    _api_base_url: str
    _client_id: str | None
    _client_secret: str | None
    _closed: bool
    _owns_session: bool
    _request_timeout: ClientTimeout
    _sesision: ClientSession | None
    _token_expires_at: float
    _token_lock: Lock
    _uses_external_token: bool

    def __init__(
            self,
            *,
            client_id: str | None = None,
            client_secret: str | None = None,
            access_token: str | None = None,
            session: ClientSession | None = None,
            request_timeout: float = 15.0,
            api_base_url: str = _DEFAULT_API_BASE_URL,
            accounts_base_url: str = _DEFAULT_ACCOUNTS_BASE_URL
    ) -> None:
        """Initialize a Spotify Web API client.

        Exactly one authentication method must be configured. Supply either a
        client identifier and secret or an externally managed access token.

        Args:
            client_id:
                The Spotify application client identifier.
            client_secret:
                The Spotify application client secret.
            access_token:
                An optional externally managed Spotify bearer token.
            session:
                An optional externally managed HTTP client session.
            request_timeout:
                The maximum duration of an individual request in seconds.
            api_base_url:
                The base URL used for Spotify Web API requests.
            accounts_base_url:
                The base URL used for Spotify authentication requests.

        Raises:
            ValueError:
                The authentication configuration, request timeout, or base URL
                is invalid.
        """

        normalized_client_id: str | None = self._normalize_optional_text(client_id)
        normalized_client_secret: str | None = self.normalize_optional_text(client_secret)
        normalized_access_token: str | None = self._normalize_optional_text(access_token)
        normalized_api_base_url: str = api_base_url.strip().rstrip("/")
        normalized_accounts_base_url: str = accounts_base_url.strip().rstrip("/")

        has_client_credentials: bool = (
            normalized_client_id is not None
            and normalized_client_secret is not None
        )
        has_partial_client_credentials: bool = (
            normalized_client_id is None
        ) is not (normalized_client_secret is None)

        if has_partial_client_credentials:
            raise ValueError("The Spotify client identifier and secret must be supplied together.")

        if has_client_credentials == (normalized_access_token is not None):
            raise ValueError("Supply either Spotify client credentials or an access token.")

        if request_timeout <= 0.0:
            raise ValueError("The Spotify request timeout must be greater than zero.")

        if not normalized_api_base_url:
            raise ValueError("The Spotify API base URL cannot be empty.")

        if not normalized_api_base_url:
            raise ValueError("The Spotify Accounts base URL cannot be empty.")

        self._client_id = normalized_client_id
        self._client_secret = normalized_client_secret
        self._access_token = normalized_access_token
        self._api_base_url = normalized_api_base_url
        self._accounts_base_url = normalized_accounts_base_url
        self._session = session
        self._owns_session = session is None
        self._request_timeout = ClientTimeout(total=request_timeout)
        self._token_expires_at = float("inf") if normalized_access_token else 0.0
        self._token_lock = Lock()
        self._uses_external_token = normalized_access_token is not None
        self._closed = False

    @property
    def api_base_url(self) -> str:
        """Return the Spotify Web API base URL.

        Returns:
            The normalized URL used for Spotify Web API requests.
        """

        return self._api_base_url

    @property
    def accounts_base_url(self) -> str:
        """Return the Spotify Accounts base URL.

        Returns:
            The normalized URL used for authentication requests.
        """

        return self._accounts_base_url

    @property
    def closed(self) -> bool:
        """Return whether the client has been closed.

        Returns:
            ``True`` when the client can no longer perform requests.
        """

        return self._closed

    @property
    def owns_session(self) -> bool:
        """Return whether the client owns its HTTP session.

        Returns:
            ``True`` when the client created and manages its session.
        """

        return self._owns_session

    @property
    def request_timeout(self) -> float:
        """Return the configured request timeout.

        Returns:
            The maximum request duration in seconds.
        """

        return self._request_timeout.total or 0.0

    @property
    def uses_external_token(self) -> bool:
        """Return whether authentication uses an external access token.

        Returns:
            ``True`` when the token lifecycle is managed by the caller.
        """

        return self._uses_external_token

    async def fetch_track(self, track_identifier: str, *, market: str | None = None) -> _SpotifyTrackPayload:
        """Retrieve metadata for one Spotify track.

        Args:
            track_identifier:
                The unique Spotify identifier of the track.
            market:
                An optional ISO 3166-1 alpha-2 market code.

        Returns:
            The typed Spotify track payload.

        Raises:
            ValueError:
                The track identifier or market is invalid.
            ProviderError:
                The Spotify Web API request failed.
        """

        identifier: str = self._normalite_identifier(
            track_identifier,
            resource_name="track"
        )
        parameters: dict[str, str] = {}
        normalized_market: str | None = self._normalize_market(market)

        if normalized_market is not None:
            parameters["market"] = normalized_market

        payload: dict[str, object] = await self._request(
            endpoint=f"tracks/{identifier}",
            parameters=parameters
        )

        return cast(_SpotifyTrackPayload, payload)

    async def fetch_tracks(
            self,
            track_identifiers: Iterable[str],
            *,
            market: str | None = None
    ) -> _SpotifySeveralTracksResponsePayload:
        """Retrieve metadata for multiple Spotify tracks.

        Args:
            track_identifiers:
                The Spotify track identifiers to retrieve.
            market:
                An optional ISO 3166-1 alpha-2 market code.

        Returns:
            The typed response containing the requested tracks.

        Raises:
            ValueError:
                No identifiers were supplied, more than fifty unique
                identifiers were supplied, or the market is invalid.
            ProviderError:
                The Spotify Web API request failed.
        """

        identifiers: tuple[str, ...] = self._normalize_identifiers(
            track_identifiers,
            resource_name="track",
            maximum_count=self._MAXIMUM_TRACK_IDENTIFIERS
        )
        parameters: dict[str, str] = {
            "ids": ",".join(identifiers)
        }
        normalized_market: str | None = self._normalize_market(market)

        if normalized_market is not None:
            parameters["market"] = normalized_market

        payload: dict[str, object] = await self._request(
            endpoint="tracks",
            parameters=parameters
        )

        return cast(_SpotifySeveralTracksResponsePayload, payload)

    async def fetch_album(self, album_identifier: str, *, market: str | None = None) -> _SpotifyAlbumPayload:
        """Retrieve metadata for one Spotify album.

        Args:
            album_identifier:
                The unique Spotify identifier of the album.
            market:
                An optional ISO 3166-1 alpha-2 market code.

        Returns:
            The typed Spotify album payload.

        Raises:
            ValueError:
                The album identifier or market is invalid.
            ProviderError:
                The Spotify Web API request failed.
        """

        identifier: str = self._normalize_identifier(
            album_identifier,
            resource_name="album"
        )
        parameters: dict[str, str] = {}
        normalized_market: str | None = self._normalize_market(market)

        if normalized_market is not None:
            parameters["market"] = normalized_market

        payload: dict[str, object] = await self._request(
            endpoint=f"albums/{identifier}",
            parameters=parameters
        )

        return cast(_SpotifyAlbumPayload, payload)

    async def fetch_album_tracks(
            self,
            album_identifier: str,
            *,
            result_limit: int = 50,
            offset: int = 0,
            market: str | None = None
    ) -> _SpotifySimplifiedTrackPagingPayload:
        """Retrieve one page of tracks from a Spotify album.

        Args:
            album_identifier:
                The unique Spotify identifier of the album.
            result_limit:
                The maximum number of tracks returned on the page.
            offset:
                The zero-based index of the first track to return.
            market:
                An optional ISO 3166-1 alpha-2 market code.

        Returns:
            The typed page containing simplified Spotify tracks.

        Raises:
            ValueError:
                The identifier, pagination values, or market is invalid.
            ProviderError:
                The Spotify Web API request failed.
        """

        identifier: str = self._normalize_identifier(
            album_identifier,
            resource_name="album"
        )
        self._validate_pagination(
            result_limit=result_limit,
            offset=offset,
            maximum_limit=self._MAXIMUM_PAGE_SIZE
        )

        parameters: dict[str, str] = {
            "limit": str(result_limit),
            "offset": str(offset)
        }
        normalized_market: str | None = self.normalize_market(market)

        if normalized_market is not None:
            parameters["market"] = normalized_market

        payload: dict[str, object] = await self._request(
            endpoint=f"albums/{identifier}/tracks",
            parameters=parameters
        )

        return cast(_SpotifySimplifiedTrackPagingPayload, payload)

    async def fetch_playlist(self, playlist_identifier: str, *, market: str | None = None) -> _SpotifyPlaylistPayload:
        """Retrieve metadata for one Spotify playlist.

        Args:
            playlist_identifier:
                The unique Spotify identifier of the playlist.
            market:
                An optional ISO 3166-1 alpha-2 market code.

        Returns:
            The typed Spotify playlist payload.

        Raises:
            ValueError:
                The playlist identifier or market is invalid.
            ProviderError:
                The Spotify Web API request failed.
        """

        identifier: str = self._normalize_identifier(
            playlist_identifier,
            resource_name="playlist"
        )
        parameters: dict[str, str] = {
            "additional_types": "track"
        }
        normalized_market: str | None = self._normalize_market(market)

        if normalized_market is not None:
            parameters["market"] = normalized_market

        payload: dict[str, object] = await self._request(
            endpoint=f"playlists/{identifier}",
            parameters=parameters
        )

        return cast(_SpotifyPlaylistPayload, payload)

    async def fetch_playlist_items(
            self,
            playlist_identifier: str,
            *,
            result_limit: int = 50,
            offset: int = 0,
            market: str | None = None
    ) -> _SpotifyPlaylistItemPagingPayload:
        """Retrieve one page of items from a Spotify playlist.

        Spotify may require a user-authorized access token for this endpoint,
        depending on playlist ownership and collaboration permissions.

        Args:
            playlist_identifier:
                The unique Spotify identifier of the playlist.
            result_limit:
                The maximum number of playlist items returned on the page.
            offset:
                The zero-based index of the first playlist item to return.
            market:
                An optional ISO 3166-1 alpha-2 market code.

        Returns:
            The typed page containing Spotify playlist items.

        Raises:
            ValueError:
                The identifier, pagination values, or market is invalid.
            ProviderAuthenticationError:
                The configured token cannot access the playlist items.
            ProviderError:
                The Spotify Web API request failed.
        """

        identifier: str = self._normalize_identifier(
            playlist_identifier,
            resource_name="playlist"
        )
        self._validate_pagination(
            result_limit=result_limit,
            offset=offset,
            maximum_limit=self._MAXIMUM_PAGE_SIZE
        )

        parameters: dict[str, str] = {
            "additional_types": "track",
            "limit": str(result_limit),
            "offset": str(offset)
        }
        normalized_market: str | None = self._normalize_market(market)

        if normalized_market is not None:
            parameters["market"] = normalized_market

        payload: dict[str, object] = await self._request(
            endpoint=f"playlists/{identifier}/items",
            parameters=parameters
        )

        return cast(_SpotifyPlaylistItemPagingPayload, payload)

    async def search(
            self,
            query_value: str,
            *,
            resource_type: SpotifySearchResource = "track",
            result_limit: int = 10,
            offset: int = 0,
            market: str | None = None
    ) -> _SpotifySearchResponsePayload:
        """Search Spotify for catalog resources.

        Args:
            query_value:
                The text submitted to the Spotify search endpoint.
            resource_type:
                The type of Spotify resource included in the response.
            result_limit:
                The maximum number of matching resources returned.
            offset:
                The zero-based index of the first search result.
            market:
                An optional ISO 3166-1 alpha-2 market code.

        Returns:
            The typed Spotify search response.

        Raises:
            ValueError:
                The search value, pagination values, or market is invalid.
            ProviderError:
                The Spotify Web API request failed.
        """

        normalized_query_value: str = query_value.strip()

        if not normalized_query_value:
            raise ValueError("The Spotify search value cannot be empty.")

        self._validate_pagination(
            result_limit=result_limit,
            offset=offset,
            maximum_limit=self._MAXIMUM_PAGE_SIZE,
            maximum_offset=self._MAXIMUM_SEARCH_OFFSET
        )

        parameters: dict[str, str] = {
            "limit": str(result_limit),
            "offset": str(offset),
            "q": normalized_query_value,
            "type": resource_type
        }
        normalized_market: str | None = self._normalize_market(market)

        if normalized_market is not None:
            parameters["market"] = normalized_market

        payload: dict[str, object] = await self._request(
            endpoint="search",
            parameters=parameters
        )

        return cast(_SpotifySearchResponsePayload, payload)

    async def close(self) -> None:
        """Close the internally owned HTTP session.

        Calling this method more than once has no effect. Externally supplied
        sessions remain open and must be managed by their owner.
        """

        if self._closed:
            return

        self._closed = True
        self._access_token = None
        self._token_expires_at = 0.0

        if (
            self._owns_session
            and self._sesision is not None
            and not self._session.closed
        ):
            await self._sesision.close()

    async def __aenter__(self) -> Self:
        """Enter the asynchronous client context.

        Returns:
            The active Spotify client.

        Raises:
            ProviderUnavailableError:
                The client has already been closed.
        """

        self._ensure_open()
        return self

    async def __aexit__(
            self,
            exception_type: type[BaseException] | None,
            exception: BaseException | None,
            traceback: TracebackType | None
    ) -> None:
        """Leave the asynchronous client context.

        Args:
            exception_type:
                The type of exception raised inside the context, when present.
            exception:
                The exception raised inside the context, when present.
            traceback:
                The traceback associated with the exception, when present.
        """

        await self.close()

    async def _request(self, endpoint: str, parameters: Mapping[str, str] | None = None) -> dict[str, object]:
        """Perform an authenticated Spotify Web API request.

        Internally managed access tokens are refreshed once after an
        unauthorized response. External tokens are never refreshed
        automatically.

        Args:
            endpoint:
                The API endpoint relative to the configured base URL.
            parameters:
                The optional query parameters included in the request.

        Returns:
            The decoded Spotify JSON response.

        Raises:
            ProviderAuthenticationError:
                Spotify rejected the configured authentication.
            ProviderRateLimitError:
                Spotify rejected the request due to rate limiting.
            ProviderRequestError:
                Spotify rejected the request for another reason.
            ProviderUnavailableError:
                Spotify or the network connection is unavailable.
        """

        normalized_endpoint: str = endpoint.strip().strip("/")

        if not normalized_endpoint:
            raise ValueError("The Spotify API endpoint cannot be empty.")

        session: ClientSession = self._get_session()

        for attempt in range(2):
            access_token: str = await self._get_access_token()

            try:
                async with session.get(
                    f"{self._api_base_url}/{normalized_endpoint}",
                    headers={
                        "Authorization": f"Bearer {access_token}"
                    },
                    params=dict(parameters or {}),
                    timeout=self._request_timeout
                ) as response:
                    payload: dict[str, object] = (
                        await self._decode_response_payload(
                            response_status=response.status,
                            response=response
                        )
                    )

                    if (
                        response.status == HTTPStatus.UNAUTHORIZED
                        and not self._uses_external_token
                        and attempt == 0
                    ):
                        self._access_token = None
                        self._token_expires_at = 0.0
                        continue

                    if response.status >= HTTPStatus.BAD_REQUEST:
                        self._raise_response_error(
                            status_code=response.status,
                            payload=payload,
                            retry_after=response.headers.get("Retry-After")
                        )

                    return payload
            except (
                ProviderAuthenticationError,
                ProviderRateLimitError,
                ProviderRequestError,
                ProviderUnavailableError
            ):
                raise
            except (ClientError, TimeoutError) as exception:
                raise ProviderUnavailableError(
                    provider_name=self._PROVIDER_NAME,
                    reason=str(exception) or exception.__class__.__name__
                ) from exception
        raise ProviderAuthenticationError(
            provider_name=self._PROVIDER_NAME,
            reason="Spotify rejected the refreshed access token."
        )

    async def _request_access_token(self) -> str:
        """Request a client-credentials access token from Spotify Accounts.

        Returns:
            The valid bearer token returned by Spotify.

        Raises:
            ProviderAuthenticationError:
                Spotify rejected the client credentials or token response.
            ProviderRateLimitError:
                Spotify rate limited the token request.
            ProviderUnavailableError:
                Spotify Accounts or the network is unavailable.
        """

        if self._client_id is None or self._client_secret is None:
            raise ProviderAuthenticationError(
                provider_name=self._PROVIDER_NAME,
                reason="Spotify client credentials are unavailable.",
            )

        session: ClientSession = self._get_session()

        try:
            async with session.post(
                f"{self._accounts_base_url}/api/token",
                auth=BasicAuth(
                    login=self._client_id,
                    password=self._client_secret,
                ),
                data={
                    "grant_type": "client_credentials",
                },
                timeout=self._request_timeout,
            ) as response:
                payload: dict[str, object] = (
                    await self._decode_response_payload(
                        response_status=response.status,
                        response=response,
                    )
                )

                if response.status == HTTPStatus.TOO_MANY_REQUESTS:
                    raise ProviderRateLimitError(
                        provider_name=self._PROVIDER_NAME,
                        retry_after=self._parse_retry_after(
                            response.headers.get("Retry-After")
                        ),
                    )

                if response.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
                    raise ProviderUnavailableError(
                        provider_name=self._PROVIDER_NAME,
                        reason=self._extract_error_message(payload),
                    )

                if response.status >= HTTPStatus.BAD_REQUEST:
                    raise ProviderAuthenticationError(
                        provider_name=self._PROVIDER_NAME,
                        reason=self._extract_error_message(payload),
                    )

                token_payload: _SpotifyAccessTokenPayload = cast(_SpotifyAccessTokenPayload, payload)
                access_token: object = token_payload.get("access_token")
                expires_in: object = token_payload.get("expires_in")

                if (
                    not isinstance(access_token, str)
                    or not access_token.strip()
                ):
                    raise ProviderAuthenticationError(
                        provider_name=self._PROVIDER_NAME,
                        reason="Spotify returned an invalid access token.",
                    )

                if (
                    not isinstance(expires_in, int)
                    or isinstance(expires_in, bool)
                    or expires_in <= 0
                ):
                    raise ProviderAuthenticationError(
                        provider_name=self._PROVIDER_NAME,
                        reason="Spotify returned an invalid token lifetime.",
                    )

                self._access_token = access_token.strip()
                self._token_expires_at = monotonic() + max(
                    0.0,
                    float(expires_in) - self._TOKEN_EXPIRATION_BUFFER,
                )

                return self._access_token
        except (
            ProviderAuthenticationError,
            ProviderRateLimitError,
            ProviderRequestError,
            ProviderUnavailableError,
        ):
            raise
        except (ClientError, TimeoutError) as exception:
            raise ProviderUnavailableError(
                provider_name=self._PROVIDER_NAME,
                reason=str(exception) or exception.__class__.__name__,
            ) from exception

    async def _get_access_token(self) -> str:
        """Return a valid Spotify access token.

        Returns:
            The external token or a cached client-credentials token.

        Raises:
            ProviderAuthenticationError:
                Spotify could not issue a valid access token.
        """

        self._ensure_open()

        if self._uses_external_token:
            if self._access_token is None:
                raise ProviderAuthenticationError(
                    provider_name=self._PROVIDER_NAME,
                    reason="The external Spotify access token is unavailable."
                )

            return self._access_token

        if (
            self._access_token is not None
            and monotonic() < self._token_expires_at
        ):
            return self._access_token

        async with self._token_lock:
            if (
                self._access_token is not None
                and monotonic() < self._token_expires_at
            ):
                return self._access_token

            return await self._request_access_token()

    async def _decode_response_payload(self, *, response_status: int, response: object) -> dict[str, object]:
        """Decode and validate a Spotify JSON response.

        Args:
            response_status:
                The HTTP status code associated with the response.
            response:
                The aiohttp response object to decode.

        Returns:
            The decoded JSON object.

        Raises:
            ProviderRequestError:
                The response does not contain a valid JSON object.
        """

        if not hasattr(response, "json"):
            raise ProviderRequestError(
                provider_name=self._PROVIDER_NAME,
                status_code=response_status,
                reason="Spotify returned an invalid HTTP response object."
            )

        try:
            raw_payload: object = await response.json(content_type=None)
        except ValueError as exception:
            raise ProviderRequestError(
                provider_name=self._PROVIDER_NAME,
                status_code=response_status,
                reason="Spotify returned an invalid JSON response."
            ) from exception

        if not isinstance(raw_payload, dict):
            raise ProviderRequestError(
                provider_name=self._PROVIDER_NAME,
                status_code=response_status,
                reason="Spotify returned an unexpected response type."
            )

        return cast(dict[str, object], raw_payload)

    def _get_session(self) -> ClientSession:
        """Return an active HTTP client session.

        Returns:
            The external or internally created HTTP session.

        Raises:
            ProviderUnavailableError:
                The Spotify client or session has been closed.
        """

        self._ensure_open()

        if self._session is None:
            self._session = ClientSession()

        if self._session.closed:
            raise ProviderUnavailableError(
                provider_name=self._PROVIDER_NAME,
                reason="The HTTP client session has already been closed."
            )

        return self._session

    def _raise_response_error(self, *, status_code: int, payload: Mapping[str, object], retry_after: str | None) -> None:
        """Convert an unsuccessful Spotify response into an exception.

        Args:
            status_code:
                The HTTP status code returned by Spotify.
            payload:
                The decoded Spotify error response.
            retry_after:
                The optional retry delay returned by Spotify.

        Raises:
            ProviderAuthenticationError:
                Authentication or authorization failed.
            ProviderRateLimitError:
                Spotify rate limited the request.
            ProviderRequestError:
                Spotify rejected the request for another reason.
            ProviderUnavailableError:
                Spotify is temporarily unavailable.
        """

        error_message: str | None = self._extract_error_message(payload)

        if status_code == HTTPStatus.TOO_MANY_REQUESTS:
            raise ProviderRateLimitError(
                provider_name=self._PROVIDER_NAME,
                retry_after=self._parse_retry_after(retry_after)
            )

        if status_code in {
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN
        }:
            raise ProviderAuthenticationError(
                provider_name=self._PROVIDER_NAME,
                reason=error_message
            )

        if status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
            raise ProviderUnavailableError(
                provider_name=self._PROVIDER_NAME,
                reason=error_message
            )

        raise ProviderRequestError(
            provider_name=self._PROVIDER_NAME,
            status_code=status_code,
            reason=error_message
        )

    @staticmethod
    def _extract_error_message(payload: Mapping[str, object]) -> str | None:
        """Extract an error description from a Spotify response.

        Args:
            payload:
                The decoded Spotify API or Accounts response.

        Returns:
            The normalized error description, when available.
        """

        raw_error: object = payload.get("error")

        if isinstance(raw_error, str):
            token_error_payload: _SpotifyTokenErrorResponsePayload = cast(
                _SpotifyTokenErrorResponsePayload,
                payload
            )
            description: object = token_error_payload.get("error_description")

            if isinstance(description, str) and description.strip():
                return description.strip()

            return raw_error.strip() or None

        if isinstance(raw_error, dict):
            raw_message: object = raw_error.get("message")

            if isinstance(raw_message, str) and raw_message.strip():
                return raw_message.strip()

        return None

    @staticmethod
    def _normalize_identifier(identifier: str, *, resource_name: str) -> str:
        """Normalize and validate one Spotify resource identifier.

        Args:
            identifier:
                The raw Spotify resource identifier.
            resource_name:
                The human-readable resource name used in error messages.

        Returns:
            The normalized non-empty identifier.

        Raises:
            ValueError:
                The supplied identifier is empty.
        """

        normalized_identifier: str = identifier.strip()

        if not normalized_identifier:
            raise ValueError(f"The Spotify {resource_name} identifier cannot be empty.")

        return normalized_identifier

    @classmethod
    def _normalize_identifiers(cls, identifiers: Iterable[str], *, resource_name: str, maximum_count: int) -> tuple[str, ...]:
        """Normalize and validate multiple Spotify identifiers.

        Args:
            identifiers:
                The raw Spotify resource identifiers.
            resource_name:
                The human-readable resource name used in error messages.
            maximum_count:
                The maximum number of unique identifiers allowed.

        Returns:
            The unique identifiers in their original iteration order.

        Raises:
            ValueError:
                No valid identifiers were supplied or the maximum was exceeded.
        """

        normalized_identifiers: list[str] = []
        known_identifiers: set[str] = set()

        for identifier in identifiers:
            normalized_identifier: str = identifier.strip()

            if (
                not normalized_identifier
                or normalized_identifier in known_identifiers
            ):
                continue

            known_identifiers.add(normalized_identifier)
            normalized_identifiers.append(normalized_identifier)

        if not normalized_identifiers:
            raise ValueError(f"At least one Spotify {resource_name} identifier is required.")

        if len(normalized_identifiers) > maximum_count:
            raise ValueError(
                f"A maximum of {maximum_count} Spotify {resource_name} "
                "identifiers may be requested at once."
            )

        return tuple(normalized_identifiers)

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
                The supplied market is not a two-letter alphabetic code.
        """

        if market is None:
            return None

        normalized_market: str = market.strip().upper()

        if len(normalized_market) != 2 or not normalized_market.isalpha():
            raise ValueError("The Spotify market must be a two-letter alphabetic code.")

        return normalized_market

    @staticmethod
    def _validate_pagination(*, result_limit: int, offset: int, maximum_limit: int, maximum_offset: int | Noen = None) -> None:
        """Validate Spotify pagination values.

        Args:
            result_limit:
                The maximum number of resources returned.
            offset:
                The zero-based index of the first resource.
            maximum_limit:
                The largest permitted result limit.
            maximum_offset:
                The largest permitted offset, when restricted.

        Raises:
            ValueError:
                The result limit or offset is outside the supported range.
        """

        if not 1 <= result_limit <= maximum_limit:
            raise ValueError(
                f"The Spotify result limit must be between 1 and "
                f"{maximum_limit}."
            )

        if offset < 0:
            raise ValueError("The Spotify result offset cannot be negative.")

        if maximum_offset is not None and offset > maximum_offset:
            raise ValueError(f"The Spotify result offset cannot exceed {maximum_offset}.")

    @staticmethod
    def _parse_retry_after(retry_after: str | None) -> float | None:
        """Parse an optional rate-limit retry delay.

        Args:
            retry_after:
                The raw Retry-After response header.

        Returns:
            The non-negative delay in seconds, or ``None`` when unavailable.
        """

        if retry_after is None:
            return None

        try:
            parsed_retry_after: float = float(retry_after)
        except ValueError:
            return None

        return max(0.0, parsed_retry_after)

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        """Normalize an optional text value.

        Args:
            value:
                The optional text value to normalize.

        Returns:
            The stripped text, or ``None`` when unavailable.
        """

        if value is None:
            return None

        normalized_value: str = value.strip()
        return normalized_value or None

    def _ensure_open(self) -> None:
        """Ensure that the Spotify client has not been closed.

        Raises:
            ProviderUnavailableError:
                The client has already been closed.
        """

        if self._closed:
            raise ProviderUnavailableError(
                provider_name=self._PROVIDER_NAME,
                reason="The Spotify client has already been closed."
            )

__all__: tuple[str, ...] = (
    "SpotifyClient",
    "SpotifySearchResource"
)
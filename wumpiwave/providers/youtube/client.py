"""Asynchronous YouTube Data API client used by WumpiWave.

This module provides typed request methods for retrieving videos, search
results, playlists, and playlist items from the YouTube Data API.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from http import HTTPStatus
from types import TracebackType
from typing import Literal, Self, cast

from aiohttp import ClientError, ClientSession, ClientTimeout

from ...exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderUnavailableError,
)
from .models import (
    _YouTubePlaylistItemListResponsePayload,
    _YouTubePlaylistListResponsePayload,
    _YouTubeSearchListResponsePayload,
    _YouTubeVideoListResponsePayload,
)

type YouTubeSearchResource = Literal["channel", "playlist", "video"]

class YouTubeClient:
    """Provide asynchronous access to the YouTube Data API.

    The client retrieves raw YouTube response payloads for videos, searches,
    playlists, and playlist items. Payload normalization into public WumpiWave
    models is handled separately by the YouTube metadata parser.

    A client session may be supplied by the caller. Otherwise, the client
    creates and owns a session lazily when the first request is performed.
    Sessions supplied by callers are never closed automatically.

    Attributes:
        base_url:
            The normalized base URL used for YouTube Data API requests.
        closed:
            Whether the client has been closed.
        owns_session:
            Whether the client owns and manages its HTTP session.
        request_timeout:
            The maximum duration of an individual request in seconds.

    Methods:
        fetch_videos:
            Retrieve metadata for one or more YouTube videos.
        search:
            Search YouTube for videos, playlists, or channels.
        fetch_playlists:
            Retrieve metadata for one or more YouTube playlists.
        fetch_playlist_items:
            Retrieve one page of items from a YouTube playlist.
        close:
            Close the internally owned HTTP session.
        __aenter__:
            Enter the asynchronous client context.
        __aexit__:
            Leave the asynchronous client context and close the client.
        _request:
            Perform a typed request to the YouTube Data API.
        _get_session:
            Return an active HTTP session.
        _raise_response_error:
            Convert an unsuccessful API response into a WumpiWave exception.
        _extract_error_details:
            Extract an error message and reason values from an API response.
        _normalize_identifiers:
            Normalize and validate provider resource identifiers.
        _validate_result_limit:
            Validate a YouTube result limit.
        _normalize_optional_value:
            Normalize an optional query parameter.
        _ensure_open:
            Ensure that the client has not been closed.
    """

    __slots__ = (
        "_api_key",
        "_base_url",
        "_closed",
        "_owns_session",
        "_request_timeout",
        "_session"
    )

    _DEFAULT_BASE_URL: str = "https://www.googleapis.com/youtube/v3"
    _MAXIMUM_RESULT_LIMIT: int = 50
    _PROVIDER_NAME: str = "youtube"
    _RATE_LIMIT_REASONS: frozenset[str] = frozenset(
        {
            "dailyLimitExceeded",
            "quotaExceeded",
            "rateLimitExceeded",
            "servingLimitExceeded",
            "uploadRateLimitExceeded",
            "userRateLimitExceeded",
        }
    )

    _api_key: str
    _base_url: str
    _closed: bool
    _owns_session: bool
    _request_timeout: ClientTimeout
    _session: ClientSession | None

    def __init__(self, api_key: str, *, session: ClientSession | None = None, request_timeout: float = 15.0,
                 base_url: str = _DEFAULT_BASE_URL) -> None:
        """Initialize a YouTube Data API client.

        Args:
            api_key:
                The API key used to authenticate YouTube Data API requests.
            session:
                An optional externally managed HTTP client session.
            request_timeout:
                The maximum duration of an individual request in seconds.
            base_url:
                The base URL used for YouTube Data API requests.

        Raises:
            ValueError:
                The API key, base URL, or request timeout is invalid.
        """

        normalized_api_key = api_key.strip()
        normalized_base_url = base_url.strip().rstrip("/")

        if not normalized_api_key:
            raise ValueError("The YouTube API key cannot be empty.")

        if not normalized_base_url:
            raise ValueError("The YouTube API base URL cannot be empty.")

        if request_timeout <= 0.0:
            raise ValueError("The YouTube request timeout must be greater than zero.")

        self._api_key = normalized_api_key
        self._base_url = normalized_base_url
        self._session = session is None
        self._request_timeout = ClientTimeout(total=request_timeout)
        self._closed = False

    @property
    def base_url(self) -> str:
        """Return the YouTube Data API base URL.

        Returns:
            The normalized base URL used for API requests.
        """

        return self._base_url

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

    async def fetch_videos(self, video_identifiers: Iterable[str], *,
                           include_statistics: bool = True) -> _YouTubeVideoListResponsePayload:
        """Retrieve metadata for one or more YouTube videos.

        Args:
            video_identifiers:
                The unique YouTube video identifiers to retrieve.
            include_statistics:
                Whether public video statistics should be requested.

        Returns:
            The typed YouTube video list response.

        Raises:
            ValueError:
                No valid identifiers were supplied or more than fifty unique
                identifiers were requested.
            ProviderError:
                The YouTube Data API request failed.
        """

        identifiers: tuple[str, ...] = self._normalize_identifiers(
            video_identifiers,
            resource_name="video"
        )
        requested_parts: list[str] = [
            "contentDetails",
            "snippet"
        ]

        if include_statistics:
            requested_parts.append("statistics")

        payload: dict[str, object] = await self._request(
            endpoint="videos",
            parameters={
                "id:": ",".join(identifiers),
                "part": ",".join(requested_parts)
            }
        )

        return cast(_YouTubeVideoListResponsePayload, payload)

    async def search(
            self,
            query_value: str,
            *,
            result_limit: int = 25,
            resource_type: YouTubeSearchResource = "video",
            page_token: str | None = None
    ) -> _YouTubeVideoListResponsePayload:
        """Search YouTube for matching media resources.

        Args:
            query_value:
                The search text submitted to YouTube.
            result_limit:
                The maximum number of search results returned on the page.
            resource_type:
                The YouTube resource type included in the search results.
            page_token:
                The pagination token used to retrieve another result page.

        Returns:
            The typed YouTube search list response.

        Raises:
            ValueError:
                The search value or result limit is invalid.
            ProviderError:
                The YouTube Data API request failed.
        """

        normalized_query_value: str = query_value.strip()

        if not normalized_query_value:
            raise ValueError("The YouTube search value cannot be empty.")

        self._validate_result_limit(result_limit)

        parameters: dict[str, str] = {
            "maxResults": str(result_limit),
            "part": "snippet",
            "q": normalized_query_value,
            "type": resource_type
        }
        normalized_page_token: str | None = self._normalize_optional_value(page_token)

        if normalized_page_token is not None:
            parameters["pageToken"] = normalized_page_token

        payload: dict[str, object] = await self._request(
            endpoint="search",
            parameters=parameters
        )

        return cast(_YouTubeSearchListResponsePayload, payload)

    async def fetch_playlist(self, playlist_identifiers: Iterable[str]) -> _YouTubePlaylistListResponsePayload:
        """Retrieve metadata for one or more YouTube playlists.

        Args:
            playlist_identifiers:
                The unique YouTube playlist identifiers to retrieve.

        Returns:
            The typed YouTube playlist list response.

        Raises:
            ValueError:
                No valid identifiers were supplied or more than fifty unique
                identifiers were requested.
            ProviderError:
                The YouTube Data API request failed.
        """

        identifiers: tuple[str, ...] = self._normalize_identifiers(
            playlist_identifiers,
            resource_name="playlist"
        )
        payload: dict[str, object] = await self._request(
            endpoint="playlist",
            parameters={
                "id": ",".join(identifiers),
                "part": "contentDetails,snippet"
            }
        )

        return cast(_YouTubeSearchListResponsePayload, payload)

    async def fetch_playlist_items(self, playlist_identifier: str, *, result_limit: int = 50, page_token: str | None = None) -> _YouTubePlaylistListResponsePayload:
        """Retrieve one page of items from a YouTube playlist.

        Args:
            playlist_identifier:
                The unique identifier of the YouTube playlist.
            result_limit:
                The maximum number of playlist items returned on the page.
            page_token:
                The pagination token used to retrieve another result page.

        Returns:
            The typed YouTube playlist item list response.

        Raises:
            ValueError:
                The playlist identifier or result limit is invalid.
            ProviderError:
                The YouTube Data API request failed.
        """

        normalized_playlist_identifier: str = playlist_identifier.strip()

        if not normalized_playlist_identifier:
            raise ValueError("The YouTube playlist identifier cannot be empty.")

        self._validate_result_limit(result_limit)

        parameters: dict[str, str] = {
            "maxResults": str(result_limit),
            "part": "contentDetails,snippet",
            "playlistId": normalized_playlist_identifier
        }
        normalized_page_token: str | None = self._normalize_optional_value(page_token)

        if normalized_page_token is not None:
            parameters["pageToken"] = normalized_page_token

            payload: dict[str, object] = await self._request(
                endpoint="playlistItems",
                parameters=parameters
            )

            return cast(_YouTubeSearchListResponsePayload, payload)

    async def close(self) -> None:
        """Close the internally owned HTTP session.

        Calling this method more than once has no effect. Externally supplied
        sessions remain open and must be managed by their owner.
        """

        if self._closed:
            return

        self._closed = True

        if (
            self._owns_session
            and self._session is not None
            and not self._session.closed
        ):
            await self._session.close()

    async def __aenter__(self) -> Self:
        """Enter the asynchronous client context.

        Returns:
            The active YouTube client.

        Raises:
            ProviderUnavailableError:
                The client has already been closed.
        """

        self._ensure_open()
        return self

    async def __aexit__(
            self,
            exception_type: type[BaseException],
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

    async def _request(self, endpoint: str, parameters: Mapping[str, str]) -> dict[str, object]:
        """Perform a request to the YouTube Data API.

        Args:
            endpoint:
                The API endpoint relative to the configured base URL.
            parameters:
                The query parameters included in the request.

        Returns:
            The decoded JSON response object.

        Raises:
            ProviderAuthenticationError:
                The request could not be authenticated.
            ProviderRateLimitError:
                The YouTube quota or request limit was exceeded.
            ProviderRequestError:
                The request or returned response was invalid.
            ProviderUnavailableError:
                The YouTube API or network connection is unavailable.
        """

        normalized_endpoint: str = endpoint.strip().strip("/")

        if not normalized_endpoint:
            raise ValueError("The YouTube API endpoint cannot be empty.")

        session: ClientSession = self._get_session()
        request_parameters: dict[str, str] = dict(parameters)
        request_parameters["key"] = self._api_key

        try:
            async with session.get(
                f"{self._base_url}/{normalized_endpoint}",
                params=request_parameters,
                timeout=self._request_timeout
            ) as response:
                try:
                    response_payload: object = await response.json(content_type=None)
                except ValueError as exception:
                    raise ProviderRequestError(
                        provider_name=self._PROVIDER_NAME,
                        status_code=response.status,
                        reason="The API returned an invalid JSON response."
                    ) from exception

                if not isinstance(response_payload, dict):
                    raise ProviderRequestError(
                        provider_name=self._PROVIDER_NAME,
                        status_code=response.status,
                        reason="The API returned an unexpected response type."
                    )

                payload: dict[str, object] = cast(
                    dict[str, object],
                    response_payload
                )

                if response.status >= HTTPStatus.BAD_REQUEST:
                    self._raise_response_error(
                        status_code=response.status,
                        payload=payload,
                        retry_after=response.headers.get("Retry-After")
                    )

                return payload
        except ProviderRequestError:
            raise
        except (
            ProviderAuthenticationError,
            ProviderRateLimitError,
            ProviderUnavailableError
        ):
            raise
        except (ClientError, TimeoutError) as exception:
            raise ProviderUnavailableError(
                provider_name=self._PROVIDER_NAME,
                reason=str(exception) or exception.__class__.__name__
            ) from exception

    def _get_session(self) -> ClientSession:
        """Return an active HTTP client session.

        Returns:
            The active external or internally created client session.

        Raises:
            ProviderUnavailableError:
                The YouTube client or supplied session has been closed.
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
        """Convert an unsuccessful API response into a provider exception.

        Args:
            status_code:
                The HTTP response status code returned by YouTube.
            payload:
                The decoded API error response.
            retry_after:
                The optional retry delay returned in the response headers.

        Raises:
            ProviderAuthenticationError:
                The API rejected the supplied credentials.
            ProviderRateLimitError:
                A quota or request limit was exceeded.
            ProviderRequestError:
                The request was rejected for another reason.
            ProviderUnavailableError:
                The YouTube API is temporarily unavailable.
        """

        error_message, error_reasons = self._extract_error_details(payload)

        if (
            status_code == HTTPStatus.TOO_MANY_REQUESTS
            or not self._RATE_LIMIT_REASONS.isdisjoint(error_reasons)
        ):
            parsed_retry_after: float | None = None

            if retry_after is not None:
                try:
                    parsed_retry_after = float(retry_after)
                except ValueError:
                    parsed_retry_after = None

            raise ProviderRateLimitError(
                provider_name=self._PROVIDER_NAME,
                retry_after=parsed_retry_after
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

    @staticmethod
    def _extract_error_details(payload: Mapping[str, object]) -> tuple[str | None, frozenset[str]]:
        """Extract an API error message and machine-readable reasons.

        Args:
            payload:
                The decoded YouTube API error response.

        Returns:
            The optional human-readable error message and all discovered
            machine-readable reason values.
        """

        error_payload: object = payload.get("error")

        if not isinstance(error_payload, dict):
            return None, frozenset()

        error_mapping: dict[object, object] = error_payload
        raw_message: object = error_mapping.get("message")
        message: str |  None = (
            raw_message.strip()
            if isinstance(raw_message, str) and raw_message.strip()
            else None
        )
        reasons: set[str] = set()
        raw_errors: object = error_mapping.get("errors")

        if isinstance(raw_errors, list):
            for raw_error in raw_errors:
                if not isinstance(raw_error, dict):
                    continue

                raw_reason: object = raw_error.get("reason")

                if isinstance(raw_reason, str) and raw_reason.strip():
                    reasons.add(raw_reason.strip())

        return message, frozenset(reasons)

    @classmethod
    def _normalize_identifiers(cls, identifiers: Iterable[str], *, resource_name: str) -> tuple[str, ...]:
        """Normalize and validate provider resource identifiers.

        Args:
            identifiers:
                The raw resource identifiers to normalize.
            resource_name:
                The human-readable resource name used in validation errors.

        Returns:
            The unique normalized identifiers in their original order.

        Raises:
            ValueError:
                No identifiers were supplied or more than fifty unique
                identifiers remain after normalization.
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
            raise ValueError(f"At least one YouTube {resource_name} identifier is required.")

        if len(normalized_identifiers) > cls._MAXIMUM_RESULT_LIMIT:
            raise ValueError(
                f"A maximum of {cls._MAXIMUM_RESULT_LIMIT} YouTube "
                f"{resource_name} identifiers may be requested at once."
            )

        return tuple(normalized_identifiers)

    @classmethod
    def _validate_result_limit(cls, result_limit: int) -> None:
        """Validate a YouTube API result limit.

        Args:
            result_limit:
                The maximum number of resources requested on one page.

        Raises:
            ValueError:
                The result limit is outside the supported range.
        """

        if not 1 <= result_limit <= cls._MAXIMUM_RESULT_LIMIT:
            raise ValueError(
                "The YouTube result limit must be between 1 and "
                f"{cls._MAXIMUM_RESULT_LIMIT}."
            )

    @staticmethod
    def _normalize_optional_value(value: str |None = None) -> str | None:
        """Normalize an optional string query parameter.

        Args:
            value:
                The optional value to normalize.

        Returns:
            The stripped value, or ``None`` when no usable value is available.
        """

        if value is None:
            return None

        normalized_value: str = value.strip()
        return normalized_value or None

    def _ensure_open(self) -> None:
        """Ensure that the YouTube client has not been closed.

        Raises:
            ProviderUnavailableError:
                The client has already been closed.
        """

        if self._closed:
            raise ProviderUnavailableError(
                provider_name=self._PROVIDER_NAME,
                reason="The YouTube client has already been closed."
            )

__all__: tuple[str, ...] = (
    "YouTubeClient",
    "YouTubeSearchResource"
)
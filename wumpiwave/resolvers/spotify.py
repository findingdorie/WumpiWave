"""Spotify stream resolver used by WumpiWave.

This module resolves normalized Spotify tracks by locating a matching YouTube
track and delegating stream extraction to another registered stream resolver.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from math import isfinite

from ..exceptions import (
    MediaNotFoundError,
    ProviderError,
    QueryError,
    ResolverError,
    StreamNotFoundError,
    UnsupportedMediaError,
)
from ..models import (
    MediaQuery,
    MediaSource,
    MediaTrack,
    PlayableSource,
    QueryType,
)
from ..protocols import MediaProvider, StreamResolver
from .base import BaseStreamResolver

class SpotifyResolver(BaseStreamResolver):
    """Resolve Spotify tracks through YouTube metadata and stream resolution.

    The resolver builds a YouTube search query from Spotify track metadata,
    compares the returned candidates by title, artists, duration, and livestream
    state, and delegates the selected candidate to another stream resolver.

    The supplied metadata provider must handle YouTube queries. Dependencies
    remain externally managed unless dependency cleanup is enabled explicitly.

    Attributes:
        name:
            The normalized public resolver name.
        closed:
            Whether the resolver has released its resources.
        metadata_provider:
            The YouTube metadata provider used to find matching tracks.
        stream_resolver:
            The resolver used to extract the selected YouTube stream.
        search_limit:
            The maximum number of YouTube candidates requested per track.
        search_suffix:
            The text appended to generated YouTube search queries.
        maximum_duration_difference:
            The largest permitted duration difference between matching tracks.
        minimum_match_score:
            The minimum candidate score required for stream resolution.
        closes_dependencies:
            Whether closing this resolver also closes its dependencies.

    Methods:
        supports:
            Determine whether the resolver supports a media track.
        resolve:
            Resolve a Spotify track into a playable audio source.
        _build_search_query:
            Build a YouTube search query from Spotify track metadata.
        _select_candidate:
            Select the strongest compatible YouTube search result.
        _score_candidate:
            Calculate the match score of a YouTube candidate.
        _duration_difference:
            Calculate the duration difference between two media tracks.
        _duration_score:
            Calculate a normalized duration similarity score.
        _token_coverage:
            Calculate how many expected text tokens occur in a candidate.
        _normalize_tokens:
            Normalize text into comparable lowercase tokens.
        _close:
            Release optionally owned provider and resolver dependencies.
    """

    __slots__ = (
        "_close_dependencies",
        "_maximum_duration_difference",
        "_metadata_provider",
        "_minimum_match_score",
        "_search_limit",
        "_search_suffix",
        "_stream_resolver"
    )

    _MAXIMUM_SEARCH_LIMIT: int = 50
    _TOKEN_PATTERN: re.Pattern[str] = re.compile(r"[^\W_]+", re.UNICODE)

    _close_dependencies: bool
    _maximum_duration_difference: float
    _metadata_provider: MediaProvider
    _minimum_match_score: float
    _search_limit: int
    _search_suffix: str
    _stream_resolver: StreamResolver

    def __init__(
            self,
            metadata_provider: MediaProvider,
            stream_resolver: StreamResolver,
            *,
            search_limit: int = 5,
            search_suffix: str = "official audio",
            maximum_duration_difference: float = 30.0,
            minimum_match_score: float = 0.55,
            closes_dependencies: bool = False
    ) -> None:
        """Initialize a Spotify stream resolver.

        Args:
            metadata_provider:
                The YouTube provider used to search for matching tracks.
            stream_resolver:
                The resolver used to extract streams from YouTube candidates.
            search_limit:
                The maximum number of YouTube candidates requested per track.
            search_suffix:
                The text appended to generated YouTube search queries.
            maximum_duration_difference:
                The largest permitted duration difference in seconds.
            minimum_match_score:
                The minimum candidate score required for selection.
            close_dependencies:
                Whether closing this resolver also closes its dependencies.

        Raises:
            ValueError:
                The provider source, search settings, duration tolerance, or
                minimum match score is invalid.
        """

        normalized_search_suffix: str = search_suffix.strip()

        if metadata_provider.source is not MediaSource.YOUTUBE:
            raise ValueError("The Spotify resolver requires a YouTube metadata provider.")

        if not 1 <= search_limit <= self._MAXIMUM_SEARCH_LIMIT:
            raise ValueError(
                "The Spotify resolver search limit must be between 1 and "
                f"{self._MAXIMUM_SEARCH_LIMIT}."
            )

        if not normalized_search_suffix:
            raise ValueError("The Spotify resolver search suffix cannot be empty.")

        if (
            not isfinite(maximum_duration_difference)
            or maximum_duration_difference <= 0.0
        ):
            raise ValueError("The maximum duration difference must be finite and greater than zero.")

        if not isfinite(minimum_match_score) or not 0.0 <= minimum_match_score <= 1.0:
            raise ValueError("The minimum Spotify match score must be between 0.0 and 1.0.")

        super().__init__(name="spotify")

        self._metadata_provider = metadata_provider
        self._stream_resolver = stream_resolver
        self._search_limit = search_limit
        self._search_suffix = normalized_search_suffix
        self._maximum_duration_difference = maximum_duration_difference
        self._minimum_match_score = minimum_match_score
        self._close_dependencies = closes_dependencies

    @property
    def metadata_provider(self) -> MediaProvider:
        """Return the metadata provider used for YouTube searches.

        Returns:
            The configured YouTube metadata provider.
        """

        return self._metadata_provider

    @property
    def stream_resolver(self) -> StreamResolver:
        """Return the resolver used for YouTube stream extraction.

        Returns:
            The configured YouTube-compatible stream resolver.
        """

        return self._stream_resolver

    @property
    def search_limit(self) -> int:
        """Return the maximum number of requested search candidates.

        Returns:
            The configured YouTube search result limit.
        """

        return self._search_limit

    @property
    def search_suffix(self) -> str:
        """Return the text appended to generated search queries.

        Returns:
            The configured YouTube search suffix.
        """

        return self._search_suffix

    @property
    def maximum_duration_difference(self) -> float:
        """Return the maximum permitted duration difference.

        Returns:
            The configured duration tolerance in seconds.
        """

        return self._maximum_duration_difference

    @property
    def minimum_match_score(self) -> float:
        """Return the minimum candidate match score.

        Returns:
            The configured minimum score between ``0.0`` and ``1.0``.
        """

        return self._minimum_match_score

    @property
    def closes_dependencies(self) -> bool:
        """Return whether closing the resolver closes its dependencies.

        Returns:
            ``True`` when dependencies are owned by this resolver.
        """

        return self._close_dependencies

    def supports(self, track: MediaTrack) -> bool:
        """Return whether the resolver supports a media track.

        Args:
            track:
                The normalized media track to inspect.

        Returns:
            ``True`` when the track originates from Spotify and the resolver
            remains open, otherwise ``False``.
        """

        return not self.closed and track.source is MediaSource.SPOTIFY

    async def resolve(self, track: MediaTrack) -> PlayableSource:
        """Resolve a Spotify track into a playable audio source.

        Args:
            track:
                The normalized Spotify track to resolve.

        Returns:
            The playable source extracted from the best matching YouTube track.

        Raises:
            UnsupportedMediaError:
                The supplied track does not originate from Spotify.
            StreamNotFoundError:
                No suitable YouTube track or playable stream was found.
            ResolverError:
                Searching or resolving the matching track failed.
        """

        self._ensure_open()

        if not self.supports(track):
            raise UnsupportedMediaError(track=track)

        media_query = MediaQuery(
            value=self._build_search_query(track),
            query_type=QueryType.SEARCH,
            source=MediaSource.YOUTUBE,
            limit=self._search_limit,
            include_statistics=False,
            include_collections=False
        )

        try:
            search_result = await self._metadata_provider.query(media_query)
        except MediaNotFoundError as exception:
            raise StreamNotFoundError(
                resolver_name=self.name,
                track=track
            ) from exception
        except (ProviderError, QueryError) as exception:
            raise ResolverError(
                message=(
                    f"Resolver {self.name!r} could not search for a matching "
                    f"YouTube track for {track.title!r}."
                ),
                resolver_name=self.name
            ) from exception

        candidate: MediaTrack | None = self._select_candidate(
            track=track,
            candidates=search_result.tracks
        )

        if candidate is None:
            raise StreamNotFoundError(
                resolver_name=self.name,
                track=track
            )

        try:
            return await self._stream_resolver.resolve(candidate)
        except ResolverError:
            raise
        except Exception as exception:
            raise ResolverError(
                message=(
                    f"Resolver {self.name!r} could not resolve the selected "
                    f"YouTube track {candidate.title!r}."
                ),
                resolver_name=self.name
            ) from exception

    def _build_search_query(self, track: MediaTrack) -> str:
        """Build a YouTube search query from Spotify track metadata.

        Args:
            track:
                The Spotify track whose metadata should form the search query.

        Returns:
            A search query containing artist names, title, and search suffix.
        """

        artist_names: str = " ".join(artist.name for artist in track.artists[:3])

        if artist_names:
            return (
                f"{artist_names} - {track.title} {self._search_suffix}"
            )

        return f"{track.title} {self._search_suffix}"

    def _select_candidate(self, *, track: MediaTrack, candidates: Iterable[MediaTrack]) -> MediaTrack | None:
        """Select the strongest compatible YouTube search result.

        Args:
            track:
                The original Spotify track being resolved.
            candidates:
                The YouTube tracks returned by the metadata provider.

        Returns:
            The highest-scoring compatible candidate, or ``None`` when no
            candidate reaches the configured minimum score.
        """

        selected_candidate: MediaTrack | None = None
        selected_score: float = self._minimum_match_score

        for candidate in candidates:
            if candidate.source is not MediaSource.YOUTUBE:
                continue

            if not self._stream_resolver.supports(candidate):
                continue

            duration_difference: float | None = self._duration_difference(
                track,
                candidate
            )

            if (
                duration_difference is not None
                and duration_difference > self._maximum_duration_difference
            ):
                continue

            candidate_score: float = self._score_candidate(
                track=track,
                candidate=candidate
            )

            if candidate_score < selected_score:
                continue

            if (
                selected_candidate is not None
                and candidate_score == selected_score
            ):
                continue

            selected_candidate = candidate
            selected_score = candidate_score

        return selected_candidate

    def _score_candidate(self, *, track: MediaTrack, candidate: MediaTrack) -> float:
        """Calculate the match score of a YouTube candidate.

        Args:
            track:
                The original Spotify track.
            candidate:
                The YouTube track being evaluated.

        Returns:
            A normalized candidate score between ``0.0`` and ``1.0``.
        """

        expected_title_tokens: frozenset[str] = self._normalize_tokens(track.title)
        candidate_title_tokens: frozenset[str] = self._normalize_tokens(candidate.title)
        expected_artist_tokens: frozenset[str] = self._normalize_tokens(" ".join(artist.name for artist in track.artists))
        candidate_artist_tokens: frozenset[str] = self._normalize_tokens(
            " ".join(
                (
                    candidate.title,
                    *(artist.name for artist in candidate.artists)
                )
            )
        )

        title_score: float = self._token_coverage(
            expected=expected_title_tokens,
            candidate=candidate_title_tokens
        )
        artist_core: float = (
            self._token_coverage(
                expected=expected_artist_tokens,
                candidate=candidate_artist_tokens
            )
            if expected_artist_tokens
            else 0.5
        )
        duration_score: float = self._duration_score(
            track=track,
            candidate=candidate
        )

        match_score: float = (
            title_score * 0.60
            + artist_core * 0.25
            + duration_score * 0.15
        )

        if candidate.is_live and not track.is_live:
            match_score -= 0.25

        return max(0.0, min(1.0, match_score))

    @staticmethod
    def _duration_difference(track: MediaTrack, candidate: MediaTrack) -> float | None:
        """Calculate the duration difference between two media tracks.

        Args:
            track:
                The original Spotify track.
            candidate:
                The YouTube track being evaluated.

        Returns:
            The absolute duration difference in seconds, or ``None`` when one
            of the durations is unavailable.
        """

        if track.duration is None or candidate.duration is None:
            return None

        return abs(track.duration - candidate.duration)

    def _duration_score(self, *, track: MediaTrack, candidate: MediaTrack) -> float:
        """Calculate a normalized duration similarity score.

        Args:
            track:
                The original Spotify track.
            candidate:
                The YouTube track being evaluated.

        Returns:
            A score between ``0.0`` and ``1.0``. Unknown durations receive a
            neutral score of ``0.5``.
        """

        duration_difference: float | None = self._duration_difference(
            track,
            candidate
        )

        if duration_difference is None:
            return 0.5

        return max(
            0.0,
            1.0
            - duration_difference / self._maximum_duration_difference
        )

    @staticmethod
    def _token_coverage(*, expected: frozenset[str], candidate: frozenset[str]) -> float:
        """Calculate how many expected text tokens occur in a candidate.

        Args:
            expected:
                The normalized tokens expected in the candidate.
            candidate:
                The normalized tokens found in the candidate metadata.

        Returns:
            A normalized token coverage score between ``0.0`` and ``1.0``.
        """

        if not expected:
            return 1.0

        return len(expected.intersection(candidate)) / len(expected)

    @classmethod
    def _normalize_tokens(cls, value: str) -> frozenset[str]:
        """Normalize text into comparable lowercase tokens.

        Args:
            value:
                The text whose words should be normalized.

        Returns:
            The unique case-insensitive alphanumeric tokens in the text.
        """

        return frozenset(
            match.group().casefold()
            for match in cls._TOKEN_PATTERN.finditer(value)
        )

    async def _close(self) -> None:
        """Release optionally owned provider and resolver dependencies.

        Raises:
            ExceptionGroup:
                Multiple dependencies failed while closing.
        """

        if not self._close_dependencies:
            return

        exceptions: list[Exception] = []

        for dependency in (
            self._stream_resolver,
            self._metadata_provider
        ):
            try:
                await dependency.close()
            except Exception as exception:
                exceptions.append(exception)

        if exceptions:
            raise ExceptionGroup(
                "One or more Spotify resolver dependencies failed to close.",
                exceptions
            )

__all__: tuple[str, ...] = ("SpotifyResolver",)
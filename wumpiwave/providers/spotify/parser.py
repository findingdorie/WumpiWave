"""Spotify metadata parsing components used by WumpiWave.

This module converts raw Spotify Web API payloads into source-independent
WumpiWave media models.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final, Never

from ...exceptions import ProviderRequestError
from ...models import (
    MediaArtist,
    MediaCollection,
    MediaImage,
    MediaSource,
    MediaStatistics,
    MediaTrack,
    MediaType,
)
from .models import (
    _SpotifyAlbumPayload,
    _SpotifyArtistPayload,
    _SpotifyImagePayload,
    _SpotifyPlaylistItemPagingPayload,
    _SpotifyPlaylistPayload,
    _SpotifySearchResponsePayload,
    _SpotifySimplifiedAlbumPayload,
    _SpotifySimplifiedTrackPayload,
    _SpotifyTrackPayload,
)

class SpotifyParser:
    """Convert Spotify API payloads into WumpiWave media models.

    The parser normalizes tracks, artists, artwork, albums, playlists,
    durations, popularity scores, search results, and paginated collection
    items without performing network requests.

    Attributes:
        None

    Methods:
        parse_track:
            Convert a complete Spotify track payload into a media track.
        parse_tracks:
            Convert complete Spotify track payloads into media tracks.
        parse_album_track:
            Convert a simplified album track into a media track.
        parse_album_tracks:
            Convert simplified album tracks into media tracks.
        parse_album:
            Convert a Spotify album payload into a media collection.
        parse_playlist:
            Convert a Spotify playlist payload into a media collection.
        parse_search_tracks:
            Convert Spotify track search results into media tracks.
        parse_playlist_items:
            Convert paginated Spotify playlist items into media tracks.
        _build_track:
            Build a media track from normalized Spotify metadata.
        _parse_artists:
            Convert Spotify artists into media artists.
        _parse_images:
            Convert Spotify artwork into media images.
        _parse_popularity:
            Validate and normalize a Spotify popularity score.
        _parse_duration:
            Convert a duration in milliseconds into seconds.
        _extract_external_url:
            Extract a public Spotify URL from a resource payload.
        _parse_playlist_owner:
            Convert a Spotify playlist owner into a media artist.
        _require_text:
            Validate and normalize a required text value.
        _normalize_optional_text:
            Normalize an optional text value.
        _raise_invalid_payload:
            Raise an exception for malformed Spotify metadata.
    """

    __slots__ = ()

    _PROVIDER_NAME: Final[str] = "spotify"
    _TRACK_URL_TEMPLATE: Final[str] = (
        "https://open.spotify.com/track/{identifier}"
    )
    _ALBUM_URL_TEMPLATE: Final[str] = (
        "https://open.spotify.com/album/{identifier}"
    )
    _PLAYLIST_URL_TEMPLATE: Final[str] = (
        "https://open.spotify.com/playlist/{identifier}"
    )
    _ARTIST_URL_TEMPLATE: Final[str] = (
        "https://open.spotify.com/artist/{identifier}"
    )
    _USER_URL_TEMPLATE: Final[str] = (
        "https://open.spotify.com/user/{identifier}"
    )

    @classmethod
    def parse_track(cls, payload: _SpotifyTrackPayload) -> MediaTrack:
        """Convert a complete Spotify track payload into a media track.

        Args:
            payload:
                The complete track payload returned by the Spotify Web API.

        Returns:
            The normalized WumpiWave media track.

        Raises:
            ProviderRequestError:
                The payload does not contain valid track or album metadata.
        """

        album: _SpotifySimplifiedAlbumPayload | None = payload.get("album")

        if album is None:
            cls._reaise_invalid_payload("The Spotify track payload does not contain album metadata.")

        return cls._build_track(
            payload=payload,
            album_name=cls._require_text(
                album.get("name"),
                field_name="album_name"
            ),
            album_images=album.get("images", []),
            release_date=cls._normalize_optional_text(album.get("release_date")),
            popularity=payload.get("popularity")
        )

    @classmethod
    def parse_tracks(cls, payloads: Iterable[_SpotifyTrackPayload]) -> tuple[MediaTrack, ...]:
        """Convert complete Spotify track payloads into media tracks.

        Args:
            payloads:
                The complete Spotify track payloads to convert.

        Returns:
            The normalized media tracks in their original iteration order.

        Raises:
            ProviderRequestError:
                One of the supplied payloads contains invalid metadata.
        """

        return tuple(cls.parse_track(payload) for payload in payloads)

    @classmethod
    def parse_album_track(cls, payload: _SpotifySimplifiedTrackPayload, *, album: _SpotifySimplifiedAlbumPayload) -> MediaTrack:
        """Convert a simplified Spotify album track into a media track.

        Simplified album track payloads do not contain their own album object.
        The containing album therefore supplies the album name, artwork, and
        release date.

        Args:
            payload:
                The simplified Spotify track payload to convert.
            album:
                The album containing the supplied track.

        Returns:
            The normalized WumpiWave media track.

        Raises:
            ProviderRequestError:
                The track or album payload contains invalid metadata.
        """

        return cls._build_track(
            payload=payload,
            album_name=cls._require_text(
                album.get("name"),
                field_name="album_name"
            ),
            album_images=album.get("images", []),
            release_date=cls._normalize_optional_text(album.get("release_date"))
        )

    @classmethod
    def parse_album_tracks(cls, payloads: Iterable[_SpotifySimplifiedTrackPayload], *, album: _SpotifySimplifiedAlbumPayload) -> tuple[MediaTrack, ...]:
        """Convert simplified Spotify album tracks into media tracks.

        Args:
            payloads:
                The simplified track payloads to convert.
            album:
                The album containing the supplied tracks.

        Returns:
            The normalized tracks in their original album order.

        Raises:
            ProviderRequestError:
                A track or the containing album has invalid metadata.
        """

        return tuple(
            cls.parse_album_track(
                payload,
                album=album
            )
            for payload in payloads
            if not payloads.get("is_local", False)
        )

    @classmethod
    def parse_album(cls, payload: _SpotifyAlbumPayload, *, tracks: Iterable[MediaTrack] = ()) -> MediaCollection:
        """Convert a Spotify album payload into a media collection.

        Args:
            payload:
                The complete album payload returned by the Spotify Web API.
            tracks:
                The normalized tracks contained in the album.

        Returns:
            The normalized WumpiWave album collection.

        Raises:
            ProviderRequestError:
                The payload does not contain required album metadata.
        """

        identifier: str = cls._require_text(
            payload.get("id"),
            field_name="album identifier"
        )
        title: str = cls._require_text(
            payload.get("name"),
            field_name="album name"
        )
        artists: tuple[MediaArtist, ...] = cls._parse_artists(payload.get("artists", []))

        return MediaCollection(
            identifier=identifier,
            source=MediaSource.SPOTIFY,
            media_type=MediaType.ALBUM,
            title=title,
            url=cls._extract_external_url(
                payload.get("external_urls"),
                fallback=cls._ALBUM_URL_TEMPLATE.format(identifier=identifier)
            ),
            tracks=tuple(tracks),
            thumbnails=cls._parse_images(payload.get("images", [])),
            author=artists[0] if artists else None
        )

    @classmethod
    def parse_playlist(cls, payload: _SpotifyPlaylistPayload, *, tracks: Iterable[MediaTrack] = ()) -> MediaCollection:
        """Convert a Spotify playlist payload into a media collection.

        Args:
            payload:
                The Spotify playlist payload to convert.
            tracks:
                The normalized tracks contained in the playlist.

        Returns:
            The normalized WumpiWave playlist collection.

        Raises:
            ProviderRequestError:
                The payload does not contain required playlist metadata.
        """

        identifier: str = cls._require_text(
            payload.get("id"),
            field_name="playlist identifier"
        )
        title: str = cls._require_text(
            payload.get("name"),
            field_name="playlist name"
        )
        artists: tuple[MediaArtist, ...] = cls._parse_artists(payload.get("artists", []))

        return MediaCollection(
            identifier=identifier,
            source=MediaSource.SPOTIFY,
            media_type=MediaType.PLAYLIST,
            title=title,
            url=cls._extract_external_url(
                payload.get("external_urls"),
                fallback=cls._PLAYLIST_URL_TEMPLATE.format(identifier=identifier)
            ),
            tracks=tuple(tracks),
            thumbnails=cls._parse_images(payload.get("images", [])),
            author=cls._parse_playlist_owner(payload),
            description=cls._normalize_optional_text(payload.get("description"))
        )

    @classmethod
    def parse_search_tracks(cls, payload: _SpotifySearchResponsePayload) -> tuple[MediaTrack, ...]:
        """Convert Spotify track search results into media tracks.

        Args:
            payload:
                The Spotify search response containing track results.

        Returns:
            The normalized tracks in their original search order.

        Raises:
            ProviderRequestError:
                A returned track contains invalid metadata.
        """

        track_page = payload.get("tracks")

        if track_page is None:
            return ()

        return cls.parse_tracks(track_page.get("items", []))

    @classmethod
    def parse_playlist_items(cls, payloads: Iterable[_SpotifyPlaylistItemPagingPayload]) -> tuple[MediaTrack, ...]:
        """Convert paginated Spotify playlist items into media tracks.

        Both the current ``item`` field and the legacy ``track`` field are
        supported. Null, local, and non-track resources are ignored.

        Args:
            payloads:
                The paginated Spotify playlist item responses to convert.

        Returns:
            The available normalized tracks in playlist order.

        Raises:
            ProviderRequestError:
                A returned Spotify track contains invalid metadata.
        """

        tracks: list[MediaTrack] = []

        for payload in payloads:
            for playlist_item in payload.get("items", []):
                if playlist_item.get("is_local", False):
                    continue

                track_payload: _SpotifyTrackPayload | None = (playlist_item.get("item"))

                if track_payload is None:
                    track_payload = playlist_item.get("track")

                if track_payload is None:
                    continue

                if track_payload.get("is_local", False):
                    continue

                if track_payload.get("type") != "track":
                    continue

                if cls._normalize_optional_text(track_payload.get("id")) is None:
                    continue

                tracks.append(cls.parse_track(track_payload))

        return tuple(tracks)

    @classmethod
    def _build_track(
            cls,
            *,
            payload: _SpotifySimplifiedTrackPayload,
            album_name: str,
            album_images: Iterable[_SpotifyImagePayload],
            release_date: str | None,
            popularity: int | None = None
    ) -> MediaTrack:
        """Build a media track from normalized Spotify metadata.

        Args:
            payload:
                The complete or simplified Spotify track payload.
            album_name:
                The name of the album containing the track.
            album_images:
                The artwork associated with the containing album.
            release_date:
                The provider-supplied album release date, when available.
            popularity:
                The provider-defined popularity score, when available.

        Returns:
            The normalized WumpiWave media track.

        Raises:
            ProviderRequestError:
                Required track metadata is missing or invalid.
        """

        identifier: str = cls._require_text(
            payload.get("id"),
            field_name="track identifier"
        )
        title: str = cls._require_text(
            payload.get("name"),
            field_name="track name"
        )

        return MediaTrack(
            identifier=identifier,
            source=MediaSource.SPOTIFY,
            title=title,
            url=cls._extract_external_url(
                payload.get("external_urls"),
                fallback=cls._TRACK_URL_TEMPLATE.format(identifier=identifier)
            ),
            duration=cls._parse_duration(payload.get("duration_ms")),
            artists=cls._parse_artist(payload.get("artists", [])),
            thumbnails=cls._parse_images(album_images),
            statistics=MediaStatistics(popularity_score=cls._parse_popularity(popularity)),
            album_name=album_name,
            release_date=release_date,
            is_explicit=payload.get("explicit", False)
        )

    @classmethod
    def _parse_artists(cls, payloads: Iterable[_SpotifyArtistPayload]) -> tuple[MediaArtist, ...]:
        """Convert Spotify artist payloads into media artists.

        Args:
            payloads:
                The Spotify artist payloads to convert.

        Returns:
            Every valid artist in the original provider order.

        Raises:
            ProviderRequestError:
                An artist payload contains no usable display name.
        """

        artists: list[MediaArtist] = []

        for payload in payloads:
            artist_name: str = cls._require_text(
                payload.get("name"),
                field_name="artist name"
            )

            artist_identifier: str | None = cls._normalize_optional_text(payload.get("id"))
            fallback_url: str | None = None

            if artist_identifier is not None:
                fallback_url = cls._ARTIST_URL_TEMPLATE.format(identifier=artist_identifier)

            artists.append(
                MediaArtist(
                    name=artist_name,
                    identifier=artist_identifier,
                    url=cls._extract_external_url(
                        payload.get("external_urls"),
                        fallback=fallback_url
                    )
                )
            )

        return tuple(artists)

    @classmethod
    def _parse_images(cls, payloads: Iterable[_SpotifyImagePayload]) -> tuple[MediaImage, ...]:
        """Convert Spotify image payloads into media images.

        Args:
            payloads:
                The Spotify artwork payloads to convert.

        Returns:
            Every valid image in the original provider order.
        """

        images: list[MediaImage] = []

        for payload in payloads:
            image_url: str | None = cls._normalize_optional_text(payload.get("url"))

            if image_url is None:
                continue

            width: int | None = payload.get("width")
            height: int | None = payload.get("height")

            images.append(
                MediaImage(
                    url=image_url,
                    width=width if width is not None and width > 0 else None,
                    height=height if height is not None and height > 0 else None,
                )
            )

        return tuple(images)

    @classmethod
    def _parse_popularity(cls, popularity: int | None) -> int | None:
        """Validate and normalize a Spotify popularity score.

        Args:
            popularity:
                The provider-defined popularity score, when available.

        Returns:
            The validated popularity score, or ``None`` when unavailable.

        Raises:
            ProviderRequestError:
                The popularity score is outside the supported range.
        """

        if popularity is None:
            return None

        if isinstance(popularity, bool) or not 0 <= popularity <= 100:
            cls._raise_invalid_payload("The Spotify popularity score must be between 0 and 100.")

        return popularity

    @classmethod
    def _parse_duration(cls, duration_ms: int | None) -> float | None:
        """Convert a Spotify duration in milliseconds into seconds.

        Args:
            duration_ms:
                The provider-supplied track duration in milliseconds.

        Returns:
            The track duration in seconds, or ``None`` when unavailable.

        Raises:
            ProviderRequestError:
                The duration is negative or uses an invalid value type.
        """

        if duration_ms is None:
            return None

        if isinstance(duration_ms, bool) or duration_ms < 0:
            cls._raise_invalid_payload("The Spotify duration must be a non-negative integer.")

        return duration_ms / 1_000.0

    @classmethod
    def _extract_external_url(cls, external_urls: dict[str, str] | None, *, fallback: str | None) -> str | None:
        """Extract a public Spotify URL from a resource payload.

        Args:
            external_urls:
                The public URL mapping returned by Spotify.
            fallback:
                The URL used when the response has no usable Spotify URL.

        Returns:
            The normalized Spotify URL or supplied fallback.
        """

        if external_urls is not None:
            spotify_url: str | None = cls._normalize_optional_text(external_urls.get("spotify"))

            if spotify_url is not None:
                return spotify_url

        return fallback

    @classmethod
    def _parse_playlist_owner(cls, payload: _SpotifyPlaylistPayload) -> MediaArtist | None:
        """Convert a Spotify playlist owner into a media artist.

        Args:
            payload:
                The playlist payload containing owner metadata.

        Returns:
            The normalized playlist owner, or ``None`` when unavailable.
        """

        owner = payload.get("owner")

        if owner is None:
            return None

        owner_identifier: str | None = cls._normalize_optional_text(owner.get("id"))
        owner_name: str | None = cls._normalize_optional_text(owner.get("display_name"))

        if owner is None:
            owner_name = owner_identifier

        if owner_name is None:
            return None

        fallback_url: str | None = None

        if owner_identifier is not None:
            fallback_url = cls._USER_URL_TEMPLATE.format(id=owner_identifier)

        return MediaArtist(
            name=owner_name,
            url=cls._extract_external_url(
                owner.get("externals_urls"),
                fallback=fallback_url
            )
        )

    @classmethod
    def _require_text(cls, value: str | None, *, field_name: str) -> str:
        """Validate and normalize a required text value.

        Args:
            value:
                The required text value to normalize.
            field_name:
                The human-readable field name used in error messages.

        Returns:
            The normalized non-empty text value.

        Raises:
            ProviderRequestError:
                The supplied value is missing or empty.
        """

        normalized_value: str | None = cls._normalize_optional_text(value)

        if normalized_value is None:
            cls._raise_invalid_payload(f"The Spotify {field_name} is missing or empty.")

        return normalized_value

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        """Normalize an optional text value.

        Args:
            value:
                The optional text value to normalize.

        Returns:
            The stripped value, or ``None`` when no usable text is available.
        """

        if value is None:
            return None

        normalized_value: str = value.strip()
        return normalized_value or None

    @classmethod
    def _raise_invalid_payload(cls, reason: str) -> Never:
        """Raise an exception for malformed Spotify metadata.

        Args:
            reason:
                The reason why the Spotify payload is invalid.

        Raises:
            ProviderRequestError:
                Always raised with the supplied reason.
        """

        raise ProviderRequestError(
            provider_name=cls._PROVIDER_NAME,
            reason=reason
        )

__all__: tuple[str, ...] = ("SpotifyParser",)
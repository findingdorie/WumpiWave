"""Internal Spotify API response models used by WumpiWave.

This module defines typed representations of JSON payloads returned by the
Spotify Accounts service and Spotify Web API. These models remain internal
and are converted into WumpiWave's source-independent public media models.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from typing import Required, TypedDict

class _SpotifyExternalUrlsPayload(TypedDict, total=False):
    """Represent public URLs associated with a Spotify resource.

    Attributes:
        spotify:
            The public Spotify URL of the resource.

    Methods:
        None
    """

    spotify: str

class _SpotifyImagePayload(TypedDict):
    """Represent artwork returned by the Spotify Web API.

    Attributes:
        url:
            The direct URL used to access the image.
        height:
            The image height in pixels, when available.
        width:
            The image width in pixels, when available.

    Methods:
        None
    """

    url: str
    height: int | None
    width: int | None

class _SpotifyRestrictionPayload(TypedDict):
    """Represent a restriction applied to Spotify content.

    Attributes:
        reason:
            The provider-defined reason why the content is restricted.

    Methods:
        None
    """

    reason: str

class _SpotifyExternalIdentifiersPayload(TypedDict, total=False):
    """Represent external identifiers associated with a Spotify track.

    Attributes:
        isrc:
            The International Standard Recording Code.
        ean:
            The International Article Number.
        upc:
            The Universal Product Code.

    Methods:
        None
    """

    isrc: str
    ean: str
    upc: str

class _SpotifyArtistPayload(TypedDict, total=False):
    """Represent a simplified Spotify artist.

    Attributes:
        external_urls:
            The public URLs associated with the artist.
        href:
            The Spotify Web API URL of the artist.
        id:
            The unique Spotify identifier of the artist.
        name:
            The public display name of the artist.
        type:
            The Spotify resource type.
        uri:
            The Spotify URI of the artist.

    Methods:
        None
    """

    external_urls: Required[_SpotifyExternalUrlsPayload]
    href: Required[str]
    id: Required[str]
    name: Required[str]
    type: Required[str]
    uri: Required[str]

class _SpotifySimplifiedAlbumPayload(TypedDict, total=False):
    """Represent simplified Spotify album metadata.

    Attributes:
        album_type:
            The provider-defined album classification.
        total_tracks:
            The total number of tracks contained in the album.
        available_markets:
            The markets in which the album is available.
        external_urls:
            The public URLs associated with the album.
        href:
            The Spotify Web API URL of the album.
        id:
            The unique Spotify identifier of the album.
        images:
            The available album artwork.
        name:
            The public album name.
        release_date:
            The provider-supplied album release date.
        release_date_precision:
            The precision of the supplied release date.
        restrictions:
            The restrictions applied to the album, when available.
        type:
            The Spotify resource type.
        uri:
            The Spotify URI of the album.
        artists:
            The artists associated with the album.

    Methods:
        None
    """

    album_type: Required[str]
    total_tracks: Required[int]
    available_markets: list[str]
    external_urls: Required[_SpotifyExternalUrlsPayload]
    href: Required[str]
    id: Required[str]
    images: Required[list[_SpotifyImagePayload]]
    name: Required[str]
    release_date: Required[str]
    release_date_precision: Required[str]
    restrictions: _SpotifyRestrictionPayload
    type: Required[str]
    uri: Required[str]
    artists: Required[list[_SpotifyArtistPayload]]

class _SpotifyLinkedTrackPayload(TypedDict, total=False):
    """Represent an original track replaced through track relinking.

    Attributes:
        external_urls:
            The public URLs associated with the original track.
        href:
            The Spotify Web API URL of the original track.
        id:
            The unique Spotify identifier of the original track.
        type:
            The Spotify resource type.
        uri:
            The Spotify URI of the original track.

    Methods:
        None
    """

    external_urls: _SpotifyExternalUrlsPayload
    href: str
    id: str
    type: str
    uri: str

class _SpotifySimplifiedTrackPayload(TypedDict, total=False):
    """Represent simplified Spotify track metadata.

    Attributes:
        artists:
            The artists who performed the track.
        available_markets:
            The markets in which the track is available.
        disc_number:
            The disc number containing the track.
        duration_ms:
            The total track duration in milliseconds.
        explicit:
            Whether Spotify marks the track as explicit.
        external_urls:
            The public URLs associated with the track.
        href:
            The Spotify Web API URL of the track.
        id:
            The unique Spotify identifier of the track.
        is_playable:
            Whether the track is playable in the selected market.
        linked_from:
            The original track replaced through track relinking.
        restrictions:
            The restrictions applied to the track, when available.
        name:
            The public title of the track.
        preview_url:
            The optional preview URL supplied by Spotify.
        track_number:
            The position of the track on its disc.
        type:
            The Spotify resource type.
        uri:
            The Spotify URI of the track.
        is_local:
            Whether the track represents a local file.

    Methods:
        None
    """

    artists: Required[list[_SpotifyArtistPayload]]
    available_markets: list[str]
    disc_number: Required[int]
    duration_ms: Required[int]
    explicit: Required[bool]
    external_urls: Required[_SpotifyExternalUrlsPayload]
    href: Required[str]
    id: Required[str | None]
    is_playable: bool
    linked_from: _SpotifyLinkedTrackPayload
    restrictions: _SpotifyRestrictionPayload
    name: Required[str]
    preview_url: str | None
    track_number: Required[int]
    type: Required[str]
    uri: Required[str]
    is_local: Required[bool]

class _SpotifyTrackPayload(_SpotifySimplifiedTrackPayload, total=False):
    """Represent complete Spotify track metadata.

    Attributes:
        album:
            The simplified album containing the track.
        external_ids:
            The external identifiers associated with the track.
        popularity:
            The provider-defined popularity score, when available.

    Methods:
        None
    """

    album: Required[_SpotifySimplifiedAlbumPayload]
    external_ids: Required[_SpotifyExternalIdentifiersPayload]
    popularity: int

class _SpotifyCopyrightPayload(TypedDict):
    """Represent a Spotify copyright statement.

    Attributes:
        text:
            The copyright statement.
        type:
            The provider-defined copyright classification.

    Methods:
        None
    """

    text: str
    type: str

class _SpotifySimplifiedTrackPagingPayload(TypedDict):
    """Represent a page of simplified Spotify tracks.

    Attributes:
        href:
            The Spotify Web API URL of the current page.
        limit:
            The maximum number of items included in the page.
        next:
            The URL of the next page, when available.
        offset:
            The offset of the first item in the page.
        previous:
            The URL of the previous page, when available.
        total:
            The total number of available tracks.
        items:
            The simplified tracks contained in the page.

    Methods:
        None
    """

    href: str
    limit: int
    next: str | None
    offset: int
    previous: str | None
    total: int
    items: list[_SpotifySimplifiedTrackPayload]

class _SpotifyAlbumPayload(
    _SpotifySimplifiedAlbumPayload,
    total=False,
):
    """Represent complete Spotify album metadata.

    Attributes:
        copyrights:
            The copyright statements associated with the album.
        external_ids:
            The external identifiers associated with the album.
        genres:
            The genres associated with the album, when available.
        label:
            The record label associated with the album.
        popularity:
            The provider-defined popularity score, when available.
        tracks:
            The paginated tracks contained in the album.

    Methods:
        None
    """

    copyrights: Required[list[_SpotifyCopyrightPayload]]
    external_ids: Required[_SpotifyExternalIdentifiersPayload]
    genres: list[str]
    label: Required[str]
    popularity: int
    tracks: Required[_SpotifySimplifiedTrackPagingPayload]

class _SpotifyUserPayload(TypedDict, total=False):
    """Represent a Spotify user associated with a playlist.

    Attributes:
        external_urls:
            The public URLs associated with the user.
        href:
            The Spotify Web API URL of the user.
        id:
            The unique Spotify identifier of the user.
        type:
            The Spotify resource type.
        uri:
            The Spotify URI of the user.
        display_name:
            The public display name of the user, when available.

    Methods:
        None
    """

    external_urls: Required[_SpotifyExternalUrlsPayload]
    href: Required[str]
    id: Required[str]
    type: Required[str]
    uri: Required[str]
    display_name: str | None

class _SpotifyPlaylistItemsSummaryPayload(TypedDict):
    """Represent summary information for Spotify playlist items.

    Attributes:
        href:
            The Spotify Web API URL used to retrieve the playlist items.
        total:
            The total number of items contained in the playlist.

    Methods:
        None
    """

    href: str
    total: int

class _SpotifyPlaylistItemPayload(TypedDict, total=False):
    """Represent an item contained in a Spotify playlist.

    Attributes:
        added_at:
            The timestamp at which the item was added, when available.
        added_by:
            The Spotify user who added the item, when available.
        is_local:
            Whether the item represents a local file.
        item:
            The current field containing the playlist track.
        track:
            The legacy field containing the playlist track.

    Methods:
        None
    """

    added_at: str | None
    added_by: _SpotifyUserPayload | None
    is_local: Required[bool]
    item: _SpotifyTrackPayload | None
    track: _SpotifyTrackPayload | None

class _SpotifyPlaylistItemPagingPayload(TypedDict):
    """Represent a page of Spotify playlist items.

    Attributes:
        href:
            The Spotify Web API URL of the current page.
        limit:
            The maximum number of items included in the page.
        next:
            The URL of the next page, when available.
        offset:
            The offset of the first item in the page.
        previous:
            The URL of the previous page, when available.
        total:
            The total number of available playlist items.
        items:
            The playlist items contained in the page.

    Methods:
        None
    """

    href: str
    limit: int
    next: str | None
    offset: int
    previous: str | None
    total: int
    items: list[_SpotifyPlaylistItemPayload]


type _SpotifyPlaylistItemsPayload = (
    _SpotifyPlaylistItemsSummaryPayload
    | _SpotifyPlaylistItemPagingPayload
)

class _SpotifyPlaylistPayload(TypedDict, total=False):
    """Represent Spotify playlist metadata.

    Attributes:
        collaborative:
            Whether the playlist owner allows collaborative modifications.
        description:
            The public playlist description, when available.
        external_urls:
            The public URLs associated with the playlist.
        href:
            The Spotify Web API URL of the playlist.
        id:
            The unique Spotify identifier of the playlist.
        images:
            The available playlist artwork.
        name:
            The public playlist name.
        owner:
            The Spotify user who owns the playlist.
        public:
            The public visibility state of the playlist.
        snapshot_id:
            The version identifier of the playlist.
        items:
            The current playlist item information.
        tracks:
            The legacy playlist item information.
        type:
            The Spotify resource type.
        uri:
            The Spotify URI of the playlist.

    Methods:
        None
    """

    collaborative: Required[bool]
    description: str | None
    external_urls: Required[_SpotifyExternalUrlsPayload]
    href: Required[str]
    id: Required[str]
    images: Required[list[_SpotifyImagePayload]]
    name: Required[str]
    owner: Required[_SpotifyUserPayload]
    public: bool | None
    snapshot_id: Required[str]
    items: _SpotifyPlaylistItemsPayload
    tracks: _SpotifyPlaylistItemsPayload
    type: Required[str]
    uri: Required[str]

class _SpotifyTrackPagingPayload(TypedDict):
    """Represent a page of complete Spotify tracks.

    Attributes:
        href:
            The Spotify Web API URL of the current page.
        limit:
            The maximum number of items included in the page.
        next:
            The URL of the next page, when available.
        offset:
            The offset of the first item in the page.
        previous:
            The URL of the previous page, when available.
        total:
            The total number of available tracks.
        items:
            The complete tracks contained in the page.

    Methods:
        None
    """

    href: str
    limit: int
    next: str | None
    offset: int
    previous: str | None
    total: int
    items: list[_SpotifyTrackPayload]

class _SpotifyAlbumPagingPayload(TypedDict):
    """Represent a page of simplified Spotify albums.

    Attributes:
        href:
            The Spotify Web API URL of the current page.
        limit:
            The maximum number of items included in the page.
        next:
            The URL of the next page, when available.
        offset:
            The offset of the first item in the page.
        previous:
            The URL of the previous page, when available.
        total:
            The total number of available albums.
        items:
            The albums contained in the page.

    Methods:
        None
    """

    href: str
    limit: int
    next: str | None
    offset: int
    previous: str | None
    total: int
    items: list[_SpotifySimplifiedAlbumPayload]

class _SpotifyPlaylistPagingPayload(TypedDict):
    """Represent a page of Spotify playlists.

    Attributes:
        href:
            The Spotify Web API URL of the current page.
        limit:
            The maximum number of items included in the page.
        next:
            The URL of the next page, when available.
        offset:
            The offset of the first item in the page.
        previous:
            The URL of the previous page, when available.
        total:
            The total number of available playlists.
        items:
            The playlists contained in the page.

    Methods:
        None
    """

    href: str
    limit: int
    next: str | None
    offset: int
    previous: str | None
    total: int
    items: list[_SpotifyPlaylistPayload | None]

class _SpotifySearchResponsePayload(TypedDict, total=False):
    """Represent a Spotify search response.

    Attributes:
        tracks:
            The matching Spotify tracks, when requested.
        albums:
            The matching Spotify albums, when requested.
        playlists:
            The matching Spotify playlists, when requested.

    Methods:
        None
    """

    tracks: _SpotifyTrackPagingPayload
    albums: _SpotifyAlbumPagingPayload
    playlists: _SpotifyPlaylistPagingPayload

class _SpotifySeveralTracksResponsePayload(TypedDict):
    """Represent a response containing several Spotify tracks.

    Attributes:
        tracks:
            The requested tracks in their response order.

    Methods:
        None
    """

    tracks: list[_SpotifyTrackPayload | None]

class _SpotifyAccessTokenPayload(TypedDict, total=False):
    """Represent an access token returned by Spotify Accounts.

    Attributes:
        access_token:
            The bearer token used to authenticate Web API requests.
        token_type:
            The type of access token returned by Spotify.
        expires_in:
            The token lifetime in seconds.
        scope:
            The authorization scopes associated with the token.

    Methods:
        None
    """

    access_token: Required[str]
    token_type: Required[str]
    expires_in: Required[int]
    scope: str

class _SpotifyApiErrorPayload(TypedDict):
    """Represent an error returned by the Spotify Web API.

    Attributes:
        status:
            The HTTP status code associated with the error.
        message:
            The human-readable error description.

    Methods:
        None
    """

    status: int
    message: str

class _SpotifyApiErrorResponsePayload(TypedDict):
    """Represent an unsuccessful Spotify Web API response.

    Attributes:
        error:
            The structured Spotify Web API error.

    Methods:
        None
    """

    error: _SpotifyApiErrorPayload

class _SpotifyTokenErrorResponsePayload(TypedDict, total=False):
    """Represent an unsuccessful Spotify token response.

    Attributes:
        error:
            The machine-readable authentication error.
        error_description:
            The human-readable authentication error description.

    Methods:
        None
    """

    error: Required[str]
    error_description: str

__all__: tuple[str, ...] = ()
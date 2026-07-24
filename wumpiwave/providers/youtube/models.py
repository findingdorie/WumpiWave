"""Internal YouTube API response models used by WumpiWave.

This module defines typed representations of the JSON payloads returned by
the YouTube Data API. These models remain internal and are converted into
WumpiWave's source-independent public data models by the YouTube parser.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from typing import NotRequired, Required, TypedDict

class _YouTubeThumbnailPayload(TypedDict, total=False):
    """Represent a thumbnail returned by the YouTube Data API.

    Attributes:
        url:
            The direct URL used to access the thumbnail.
        width:
            The thumbnail width in pixels, when available.
        height:
            The thumbnail height in pixels, when available.

    Methods:
        None
    """

    url: Required[str]
    width: int
    height: int

type _YouTubeThumbnailMap = dict[str, _YouTubeThumbnailPayload]

class _YouTubeLocalizedMetadataPayload(TypedDict):
    """Represent localized YouTube metadata.

    Attributes:
        title:
            The localized title of the resource.
        description:
            The localized description of the resource.

    Methods:
        None
    """

    title: str
    description: str

class _YouTubeResourceIdentifierPayload(TypedDict, total=False):
    """Represent the identifier of a YouTube search or playlist resource.

    Attributes:
        kind:
            The YouTube resource type associated with the identifier.
        videoId:
            The unique video identifier, when the resource is a video.
        playlistId:
            The unique playlist identifier, when the resource is a playlist.
        channelId:
            The unique channel identifier, when the resource is a channel.

    Methods:
        None
    """

    kind: Required[str]
    videoId: str
    playlistId: str
    channelId: str

class _YouTubeSnippetPayload(TypedDict, total=False):
    """Represent shared YouTube resource metadata.

    Attributes:
        publishedAt:
            The ISO 8601 publication timestamp of the resource.
        channelId:
            The unique identifier of the publishing channel.
        title:
            The public title of the resource.
        description:
            The public description of the resource.
        thumbnails:
            The available thumbnail variants indexed by quality name.
        channelTitle:
            The public display name of the publishing channel.
        tags:
            The tags associated with the resource, when available.
        categoryId:
            The category identifier assigned to the resource.
        liveBroadcastContent:
            The current livestream status supplied by YouTube.
        defaultLanguage:
            The language of the resource metadata, when specified.
        localized:
            Localized title and description values, when requested.
        playlistId:
            The playlist containing a playlist item.
        position:
            The zero-based position of an item inside a playlist.
        resourceId:
            The identifier of the resource referenced by a playlist item.

    Methods:
        None
    """

    publishedAt: str
    channelId: str
    title: Required[str]
    description: Required[str]
    thumbnails: Required[_YouTubeThumbnailMap]
    channelTitle: str
    tags: list[str]
    categoryId: str
    liveBroadcastContent: str
    defaultLanguage: str
    localized: _YouTubeLocalizedMetadataPayload
    playlistId: str
    position: int
    resourceId: _YouTubeResourceIdentifierPayload

class _YouTubeVideoContentDetailsPayload(TypedDict, total=False):
    """Represent technical details associated with a YouTube video.

    Attributes:
        duration:
            The ISO 8601 duration of the video.
        dimension:
            Whether the video is presented in two or three dimensions.
        definition:
            The standard or high-definition classification.
        caption:
            Whether captions are available for the video.
        licensedContent:
            Whether YouTube identifies the video as licensed content.
        projection:
            The projection format used by the video.

    Methods:
        None
    """

    duration: Required[str]
    dimension: str
    definition: str
    caption: str
    licensedContent: bool
    projection: str

class _YouTubeVideoStatisticsPayload(TypedDict, total=False):
    """Represent public statistics associated with a YouTube video.

    Attributes:
        viewCount:
            The total view count encoded as a decimal string.
        likeCount:
            The total like count encoded as a decimal string.
        favoriteCount:
            The total favorite count encoded as a decimal string.
        commentCount:
            The total comment count encoded as a decimal string.

    Methods:
        None
    """

    viewCount: str
    likeCount: str
    favoriteCount: str
    commentCount: str

class _YouTubePlaylistContentDetailsPayload(TypedDict):
    """Represent details associated with a YouTube playlist.

    Attributes:
        itemCount:
            The number of videos contained in the playlist.

    Methods:
        None
    """

    itemCount: int

class _YouTubePlaylistItemContentDetailsPayload(TypedDict, total=False):
    """Represent details associated with a YouTube playlist item.

    Attributes:
        videoId:
            The unique identifier of the referenced video.
        videoPublishedAt:
            The ISO 8601 publication timestamp of the referenced video.

    Methods:
        None
    """

    videoId: str
    videoPublishedAt: str

class _YouTubeVideoPayload(TypedDict, total=False):
    """Represent a video resource returned by the YouTube Data API.

    Attributes:
        kind:
            The YouTube resource type.
        etag:
            The entity tag associated with the resource.
        id:
            The unique identifier of the video.
        snippet:
            The normalized metadata section, when requested.
        contentDetails:
            The technical video details, when requested.
        statistics:
            The public video statistics, when requested.

    Methods:
        None
    """

    kind: Required[str]
    etag: Required[str]
    id: Required[str]
    snippet: _YouTubeSnippetPayload
    contentDetails: _YouTubeVideoContentDetailsPayload
    statistics: _YouTubeVideoStatisticsPayload

class _YouTubePlaylistPayload(TypedDict, total=False):
    """Represent a playlist resource returned by the YouTube Data API.

    Attributes:
        kind:
            The YouTube resource type.
        etag:
            The entity tag associated with the resource.
        id:
            The unique identifier of the playlist.
        snippet:
            The playlist metadata section, when requested.
        contentDetails:
            The playlist content details, when requested.

    Methods:
        None
    """

    kind: Required[str]
    etag: Required[str]
    id: Required[str]
    snippet: _YouTubeSnippetPayload
    contentDetails: _YouTubePlaylistContentDetailsPayload

class _YouTubePlaylistItemPayload(TypedDict, total=False):
    """Represent an item contained in a YouTube playlist.

    Attributes:
        kind:
            The YouTube resource type.
        etag:
            The entity tag associated with the resource.
        id:
            The unique identifier of the playlist item.
        snippet:
            The playlist item metadata section, when requested.
        contentDetails:
            The referenced video details, when requested.

    Methods:
        None
    """

    kind: Required[str]
    etag: Required[str]
    id: Required[str]
    snippet: _YouTubeSnippetPayload
    contentDetails: _YouTubePlaylistItemContentDetailsPayload

class _YouTubeSearchItemPayload(TypedDict):
    """Represent an item returned by a YouTube search request.

    Attributes:
        kind:
            The YouTube resource type.
        etag:
            The entity tag associated with the search result.
        id:
            The identifier of the referenced YouTube resource.
        snippet:
            The metadata associated with the search result.

    Methods:
        None
    """

    kind: str
    etag: str
    id: _YouTubeResourceIdentifierPayload
    snippet: _YouTubeSnippetPayload

class _YouTubePageInfoPayload(TypedDict):
    """Represent pagination information returned by the YouTube Data API.

    Attributes:
        totalResults:
            The total or estimated number of matching resources.
        resultsPerPage:
            The number of resources included in the current response.

    Methods:
        None
    """

    totalResults: int
    resultsPerPage: int

class _YouTubeVideoListResponsePayload(TypedDict, total=False):
    """Represent a YouTube video list response.

    Attributes:
        kind:
            The YouTube response resource type.
        etag:
            The entity tag associated with the response.
        nextPageToken:
            The token used to request the next response page.
        prevPageToken:
            The token used to request the previous response page.
        pageInfo:
            Pagination information associated with the response.
        items:
            The video resources returned by the request.

    Methods:
        None
    """

    kind: Required[str]
    etag: Required[str]
    nextPageToken: str
    prevPageToken: str
    pageInfo: Required[_YouTubePageInfoPayload]
    items: Required[list[_YouTubeVideoPayload]]

class _YouTubePlaylistListResponsePayload(TypedDict, total=False):
    """Represent a YouTube playlist list response.

    Attributes:
        kind:
            The YouTube response resource type.
        etag:
            The entity tag associated with the response.
        nextPageToken:
            The token used to request the next response page.
        prevPageToken:
            The token used to request the previous response page.
        pageInfo:
            Pagination information associated with the response.
        items:
            The playlist resources returned by the request.

    Methods:
        None
    """

    kind: Required[str]
    etag: Required[str]
    nextPageToken: str
    prevPageToken: str
    pageInfo: Required[_YouTubePageInfoPayload]
    items: Required[list[_YouTubePlaylistPayload]]

class _YouTubePlaylistItemListResponsePayload(TypedDict, total=False):
    """Represent a YouTube playlist item list response.

    Attributes:
        kind:
            The YouTube response resource type.
        etag:
            The entity tag associated with the response.
        nextPageToken:
            The token used to request the next response page.
        prevPageToken:
            The token used to request the previous response page.
        pageInfo:
            Pagination information associated with the response.
        items:
            The playlist items returned by the request.

    Methods:
        None
    """

    kind: Required[str]
    etag: Required[str]
    nextPageToken: str
    prevPageToken: str
    pageInfo: Required[_YouTubePageInfoPayload]
    items: Required[list[_YouTubePlaylistItemPayload]]

class _YouTubeSearchListResponsePayload(TypedDict, total=False):
    """Represent a YouTube search list response.

    Attributes:
        kind:
            The YouTube response resource type.
        etag:
            The entity tag associated with the response.
        nextPageToken:
            The token used to request the next response page.
        prevPageToken:
            The token used to request the previous response page.
        regionCode:
            The region code used to process the search.
        pageInfo:
            Pagination information associated with the response.
        items:
            The search results returned by the request.

    Methods:
        None
    """

    kind: Required[str]
    etag: Required[str]
    nextPageToken: str
    prevPageToken: str
    regionCode: str
    pageInfo: Required[_YouTubePageInfoPayload]
    items: Required[list[_YouTubeSearchItemPayload]]

class _YouTubeErrorDetailPayload(TypedDict, total=False):
    """Represent one error detail returned by the YouTube Data API.

    Attributes:
        message:
            The human-readable error description.
        domain:
            The service domain associated with the error.
        reason:
            The machine-readable reason for the error.
        location:
            The request field associated with the error.
        locationType:
            The type of request location associated with the error.

    Methods:
        None
    """

    message: Required[str]
    domain: str
    reason: str
    location: str
    locationType: str


class _YouTubeErrorPayload(TypedDict, total=False):
    """Represent a YouTube Data API error object.

    Attributes:
        code:
            The HTTP status code associated with the error.
        message:
            The human-readable error description.
        errors:
            The detailed errors returned by the API.
        status:
            The canonical status name associated with the error.

    Methods:
        None
    """

    code: Required[int]
    message: Required[str]
    errors: list[_YouTubeErrorDetailPayload]
    status: str

class _YouTubeErrorResponsePayload(TypedDict):
    """Represent an unsuccessful YouTube Data API response.

    Attributes:
        error:
            The structured error object returned by YouTube.

    Methods:
        None
    """

    error: _YouTubeErrorPayload

__all__: tuple[str, ...] = ()
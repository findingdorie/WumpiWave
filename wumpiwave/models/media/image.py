"""
Image data models used throughout WumpiWave.

This module provides a source-independent representation of thumbnails,
artwork, album covers, and other images associated with media resources.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class MediaImage:
    """
    Represents an image associated with a media resource.

    The model stores normalized image metadata independently from the provider
    that supplied it. It can represent thumbnails, album covers, artist images,
    playlist artwork, and other media-related images.

    Attributes:
        - url:
            The direct URL used to access the image.
        - width:
            The image width in pixels, when available.
        - height:
            The image height in pixels, when available.

    Methods:
        None
    """

    url: str
    width: int | None = None
    height: int | None = None

__all__: tuple[str, ...] = (
    "MediaImage",
)
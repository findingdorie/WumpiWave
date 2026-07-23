"""Artist data models used throughout WumpiWave.

This module provides a source-independent representation of an artist,
creator, channel, or other author associated with a media resource.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MediaArtist:
    """Represents an artist, creator, channel, or media author.

    The model stores normalized artist information independently from the
    provider that supplied it. Provider-specific objects must not be stored
    directly inside this model.

    Attributes:
        - name:
            The public display name of the artist or creator.
        - identifier:
            The provider-specific identifier of the artist, when available.
        - url:
            The public URL leading to the artist or creator profile.

    Methods:
        None
    """

    name: str
    identifier: str | None = None
    url: str | None = None


__all__: tuple[str, ...] = ("MediaArtist",)

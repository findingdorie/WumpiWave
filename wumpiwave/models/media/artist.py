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
        __post_init__:
            Validate the media artist metadata.
    """

    name: str
    identifier: str | None = None
    url: str | None = None

    def __post_init__(self) -> None:
        """Validate the media artist metadata.

        Raises:
            ValueError:
                The artist name, identifier, or URL is empty.
        """

        if not self.name.strip():
            raise ValueError("The media artist name cannot be empty.")

        if self.identifier is not None and not self.identifier.strip():
            raise ValueError("The media artist identifier cannot be empty.")

        if self.url is not None and not self.url.strip():
            raise ValueError("The media artist URL cannot be empty.")

__all__: tuple[str, ...] = ("MediaArtist",)

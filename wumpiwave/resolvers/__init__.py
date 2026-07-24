"""Public stream resolvers available in WumpiWave.

This package contains resolver implementations responsible for converting
normalized media tracks into temporary playable audio sources.

Resolvers expose only WumpiWave data models and must not leak implementation-
specific extraction or streaming objects through their public interfaces.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
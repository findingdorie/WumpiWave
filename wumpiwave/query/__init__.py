"""Public query processing components used throughout WumpiWave.

This package contains utilities for parsing media queries, matching supported
URLs, and routing normalized queries to compatible metadata providers.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .matcher import QueryMatcher
from .parser import QueryParser
from .router import QueryRouter

__all__: tuple[str, ...] = (
    "QueryMatcher",
    "QueryParser",
    "QueryRouter",
)
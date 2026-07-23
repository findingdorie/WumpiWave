"""
Provider exceptions raised throughout WumpiWave.

This module defines errors related to provider registration, authentication,
requests, rate limits, and service availability.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from . import QueryError
from .base import WumpiWaveError

class ProviderError(WumpiWaveError):
    """
    Represents the base exception for metadata provider errors.

    Attributes:
        - provider_name:
            The public name of the provider associated with the error.

    Methods:
        __init__:
            Initializes the exception with the provider name and message.
    """

    __slots__ = (
        "provider_name",
    )

    provider_name: str

    def __init__(self, provider_name: str, message: str) -> None:
        """
        Initialize a provider error.

        Args:
            provider_name:
                The public name of the provider associated with the error.
            message:
                The human-readable error message.
        """

        self.provider_name = provider_name
        super().__init__(message)

class ProviderAlreadyRegisteredError(ProviderError):
    """
    Represents an attempt to register an existing provider name.

    Attributes:
        - provider_name:
            The name already registered with the media client.

    Methods:
        __init__:
            Initializes the exception with the duplicate provider name.
    """

    __slots__ = ()

    def __init__(self, provider_name: str) -> None:
        """
        Initialize a provider-already-registered error.

        Args:
            provider_name:
                The duplicate provider name.
        """

        super().__init__(
            provider_name,
            f"The media provider {provider_name!r} is already registered."
        )

class ProviderNotFoundError(ProviderError):
    """
    Represents a requested provider that is not registered.

    Attributes:
        - provider_name:
            The provider name that could not be found.

    Methods:
        __init__:
            Initializes the exception with the missing provider name.
    """

    __slots__ = ()

    def __init__(self, provider_name: str) -> None:
        """
        Initialize a provider-not-found error.

        Args:
            provider_name:
                The provider name that could not be found.
        """

        super().__init__(
            provider_name,
            f"No media provider named {provider_name!r} is registered."
        )

class ProviderAuthenticationError(ProviderError):
    """
    Represents failed authentication with a metadata provider.

    Attributes:
        - provider_name:
            The provider whose authentication failed.
        - reason:
            The provider-supplied authentication failure reason, when available.

    Methods:
        __init__:
            Initializes the exception with the provider and optional reason.
    """

    __slots__ = (
        "reason",
    )

    reason: str | None

    def __init__(self, provider_name: str, reason: str | None = None) -> None:
        """
        Initialize a provider authentication error.

        Args:
            provider_name:
                The provider whose authentication failed.
            reason:
                The authentication failure reason, when available.
        """

        self.reason = reason
        super().__init__(
            provider_name,
            (
                f"Authentication with provider {provider_name!r} failed: "
                f"{reason}"
                if reason
                else f"Authentication with provider {provider_name!r} failed."
            )
        )

class ProviderRequestError(ProviderError):
    """
    Represents an unsuccessful request to a metadata provider.

    Attributes:
        - provider_name:
            The provider whose request failed.
        - status_code:
            The HTTP response status code, when available.
        - reason:
            The provider-supplied failure reason, when available.

    Methods:
        __init__:
            Initializes the exception with request failure details.
    """

    __slots__ = (
        "reason",
        "status_code"
    )

    status_code: int | None
    reason: str | None

    def __init__(self, provider_name: str, *, status_code: int | None = None, reason: str | None = None) -> None:
        """
        Initialize a provider request error.

        Args:
            provider_name:
                The provider whose request failed.
            status_code:
                The HTTP response status code, when available.
            reason:
                The provider-supplied failure reason, when available.
        """

        self.status_code = status_code
        self.reason = reason
        super().__init__(
            provider_name,
            (
                f"Request to provider {provider_name!r} failed"
                f"{f' with status code {status_code}' if status_code else ''}"
                f"{f': {reason}' if reason else '.'}"
            )
        )

class ProviderRateLimitError(ProviderError):
    """
    Represents a metadata provider rate-limit response.

    Attributes:
        - provider_name:
            The provider that rejected the request.
        - retry_after:
            The recommended delay in seconds before retrying, when available.

    Methods:
        __init__:
            Initializes the exception with optional retry information.
    """

    __slots__ = (
        "retry_after",
    )

    retry_after: float | None

    def __init__(self, provider_name: str, retry_after: float | None = None) -> None:
        """
        Initialize a provider rate-limit error.

        Args:
            provider_name:
                The provider that rejected the request.
            retry_after:
                The recommended retry delay in seconds, when available.
        """

        self.retry_after = retry_after
        super().__init__(
            provider_name,
            (
                f"Provider {provider_name!r} is rate limited. "
                f"Retry after {retry_after:g} seconds."
                if retry_after is not None
                else f"Provider {provider_name!r} is rate limited."
            )
        )

class ProviderUnavailableError(QueryError):
    """
    Represents a metadata provider that is temporarily unavailable.

    Attributes:
        - provider_name:
            The provider that is currently unavailable.
        - reason:
            The provider-supplied availability failure reason, when available.

    Methods:
        __init__:
            Initializes the exception with the provider and optional reason.
    """

    __slots__ = (
        "reason",
    )

    reason: str | None

    def __init__(self, provider_name: str, reason: str | None = None) -> None:
        """
        Initialize a provider-unavailable error.

        Args:
            provider_name:
                The provider that is currently unavailable.
            reason:
                The availability failure reason, when available.
        """

        self.reason = reason
        super().__init__(
            provider_name,
            (
                f"Provider {provider_name!r} is unavailable: {reason}"
                if reason
                else f"Provider {provider_name!r} is unavailable."
            )
        )

__all__: tuple[str, ...] = (
    "ProviderAlreadyRegisteredError",
    "ProviderAuthenticationError",
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderRateLimitError",
    "ProviderRequestError",
    "ProviderUnavailableError",
)
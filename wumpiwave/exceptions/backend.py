"""Playback backend exceptions raised throughout WumpiWave.

This module defines errors related to backend availability, voice connections,
and audio playback operations.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from .base import WumpiWaveError


class BackendError(WumpiWaveError):
    """Represent the base exception for playback backend errors.

    Attributes:
        backend_name:
            The public name of the playback backend associated with the error.

    Methods:
        __init__:
            Initialize the exception with the backend name and message.
    """

    __slots__ = ("backend_name",)

    backend_name: str

    def __init__(self, backend_name: str, message: str) -> None:
        """Initialize a playback backend error.

        Args:
            backend_name:
                The public name of the backend associated with the error.
            message:
                The human-readable error message.

        Raises:
            ValueError:
                The backend name or error message is empty.
        """

        normalized_backend_name: str = backend_name.strip()
        normalized_message: str = message.strip()

        if not normalized_backend_name:
            raise ValueError("The backend name cannot be empty.")

        if not normalized_message:
            raise ValueError("The backend error message cannot be empty.")

        self.backend_name = normalized_backend_name
        super().__init__(normalized_message)

class BackendConnectionError(BackendError):
    """Represent a failed connection to a playback backend.

    Attributes:
        backend_name:
            The name of the backend whose connection failed.
        reason:
            The connection failure reason, when available.

    Methods:
        __init__:
            Initialize the exception with the backend and optional reason.
    """

    __slots__ = ("reason",)

    reason: str | None

    def __init__(self, backend_name: str, reason: str | None = None) -> None:
        """Initialize a playback backend connection error.

        Args:
            backend_name:
                The name of the backend whose connection failed.
            reason:
                The connection failure reason, when available.
        """

        normalized_reason: str | None = (
            reason.strip() if reason is not None else None
        )

        if normalized_reason == "":
            normalized_reason = None

        self.reason = normalized_reason
        message: str = f"Backend {backend_name!r} failed to connect."

        if normalized_reason is not None:
            message = f"Backend {backend_name!r} failed to connect: {normalized_reason}."

        super().__init__(
            backend_name=backend_name,
            message=message
        )

class BackendNotConnectedError(BackendError):
    """Represent an operation requiring an active backend connection.

    Attributes:
        backend_name:
            The name of the backend that is not connected.

    Methods:
        __init__:
            Initialize the exception with the disconnected backend name.
    """

    __slots__ = ()

    def __init__(self, backend_name: str) -> None:
        """Initialize a backend-not-connected error.

        Args:
            backend_name:
                The name of the backend that is not connected.
        """

        super().__init__(
            backend_name=backend_name,
            message=f"Backend {backend_name!r} is not connected."
        )

class BackendPlaybackError(BackendError):
    """Represent a failed audio playback operation.

    Attributes:
        backend_name:
            The name of the backend whose operation failed.
        operation:
            The playback operation that could not be completed.
        reason:
            The operation failure reason, when available.

    Methods:
        __init__:
            Initialize the exception with playback operation details.
    """

    __slots__ = (
        "operation",
        "reason"
    )

    operation: str
    reason: str | None

    def __init__(self, backend_name: str, operation: str, reason: str | None = None) -> None:
        """Initialize a backend playback error.

        Args:
            backend_name:
                The name of the backend whose operation failed.
            operation:
                The playback operation that could not be completed.
            reason:
                The operation failure reason, when available.

        Raises:
            ValueError:
                The supplied playback operation is empty.
        """

        normalized_operation: str = operation.strip()
        normalized_reason: str | None = (
            reason.strip() if reason is not None else None
        )

        if not normalized_operation:
            raise ValueError("The playback operation cannot be empty.")

        if normalized_reason == "":
            normalized_reason = None

        self.operation = normalized_operation
        self.reason = normalized_reason
        message: str = (
            f"Backend {backend_name!r} failed to perform playback operation "
            f"{normalized_operation!r}."
        )

        if normalized_reason is not None:
            message = (
                f"Backend {backend_name!r} failed to perform playback "
                f"operation {normalized_operation!r}: {normalized_reason}"
            )

            super().__init__(
                backend_name=backend_name,
                message=message
            )

class BackendUnavailableError(BackendError):
    """Represent a playback backend that is temporarily unavailable.

    Attributes:
        backend_name:
            The name of the unavailable playback backend.
        reason:
            The availability failure reason, when available.

    Methods:
        __init__:
            Initialize the exception with the backend and optional reason.
    """

    __slots__ = ("reason",)

    reason: str | None

    def __init__(self, backend_name: str, reason: str | None = None) -> None:
        """Initialize a backend-unavailable error.

        Args:
            backend_name:
                The name of the unavailable playback backend.
            reason:
                The availability failure reason, when available.
        """

        normalized_reason: str | None= (
            reason.strip() if reason is not None else None
        )

        if normalized_reason == "":
            normalized_reason = None

        self.reason = normalized_reason
        message: str = f"Backend {backend_name!r} is unavailable."

        if normalized_reason is not None:
            message = (
                f"Backend {backend_name!r} is unavailable: {normalized_reason}"
            )

        super().__init__(
            backend_name=backend_name,
            message=message
        )

__all__: tuple[str, ...] = (
    "BackendConnectionError",
    "BackendError",
    "BackendNotConnectedError",
    "BackendPlaybackError",
    "BackendUnavailableError",
)
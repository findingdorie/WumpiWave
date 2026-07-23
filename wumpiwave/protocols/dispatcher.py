"""Event dispatcher protocol used throughout WumpiWave.

This module defines the structural interface required for dispatchers that
manage and invoke asynchronous playback event listeners.

Attributes:
    EventListener:
        An asynchronous callback that receives a playback event.
    EventListenerDecorator:
        A decorator used to register an asynchronous event listener.

Methods:
    None
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

from ..models import PlaybackEvent

type EventListener[EventT: PlaybackEvent] = Callable[[EventT], Awaitable[None]]
type EventListenerDecorator[EventT: PlaybackEvent] = Callable[
    [EventListener[EventT]],
    EventListener[EventT],
]

@runtime_checkable
class EventDispatcher(Protocol):
    """Define the interface required for playback event dispatchers.

    An event dispatcher stores asynchronous listeners and invokes them whenever
    matching playback events are emitted. Implementations do not need to inherit
    from this protocol as long as they provide the required attributes and
    methods.

    Attributes:
        listener_count:
            The total number of registered event listeners.

    Methods:
        add_listener:
            Register an asynchronous listener for an event type.
        remove_listener:
            Remove a previously registered event listener.
        listen:
            Create a decorator that registers an event listener.
        dispatch:
            Dispatch an event to all compatible listeners.
        clear_listeners:
            Remove listeners for one event type or every event type.
    """

    @property
    def listener_count(self) -> int:
        """Return the total number of registered event listeners.

        Returns:
            The number of listeners currently stored by the dispatcher.
        """

        ...

    def add_listener[EventT: PlaybackEvent](
        self,
        event_type: type[EventT],
        listener: EventListener[EventT],
    ) -> None:
        """Register an asynchronous listener for an event type.

        Args:
            event_type:
                The playback event class handled by the listener.
            listener:
                The asynchronous callback invoked when a compatible event is
                dispatched.

        Raises:
            ValueError:
                The listener is already registered for the supplied event type.
        """

        ...

    def remove_listener[EventT: PlaybackEvent](
        self,
        event_type: type[EventT],
        listener: EventListener[EventT],
    ) -> bool:
        """Remove an asynchronous listener from an event type.

        Args:
            event_type:
                The playback event class associated with the listener.
            listener:
                The asynchronous callback that should be removed.

        Returns:
            ``True`` when the listener was removed, otherwise ``False``.
        """

        ...

    def listen[EventT: PlaybackEvent](
        self,
        event_type: type[EventT],
    ) -> EventListenerDecorator[EventT]:
        """Create a decorator that registers an event listener.

        Args:
            event_type:
                The playback event class handled by the decorated listener.

        Returns:
            A decorator that registers and returns the supplied listener.

        Raises:
            ValueError:
                The listener is already registered for the supplied event type.
        """

        ...

    async def dispatch[EventT: PlaybackEvent](self, event: EventT) -> None:
        """Dispatch a playback event to all compatible listeners.

        Listeners registered for the exact event type and its supported base
        event types may be invoked by the dispatcher implementation.

        Args:
            event:
                The playback event that should be dispatched.

        Raises:
            ExceptionGroup:
                One or more event listeners raised an exception.
        """

        ...

    def clear_listeners(
        self,
        event_type: type[PlaybackEvent] | None = None,
    ) -> None:
        """Remove registered event listeners.

        Args:
            event_type:
                The event type whose listeners should be removed. All listeners
                are removed when no event type is supplied.
        """

        ...

__all__: tuple[str, ...] = (
    "EventDispatcher",
    "EventListener",
    "EventListenerDecorator"
)
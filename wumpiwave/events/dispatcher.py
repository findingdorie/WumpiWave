"""Asynchronous playback event dispatcher used by WumpiWave.

This module provides listener registration, removal, inspection, and parallel
dispatching for WumpiWave playback events.

Attributes:
    None

Methods:
    None
"""

from __future__ import annotations

from asyncio import TaskGroup
from collections.abc import Awaitable, Callable, Iterator
from typing import Self, cast

from ..models import PlaybackEvent

type _StoredEventListener = Callable[[PlaybackEvent], Awaitable[None]]

class PlaybackEventDispatcher:
    """Manage asynchronous listeners for WumpiWave playback events.

    Listeners are registered for a specific playback event class. Dispatching
    an event invokes listeners registered for the concrete event class and any
    compatible base event classes.

    Listener registration order is preserved. All matching listeners are
    executed concurrently within an asynchronous task group.

    Attributes:
        event_types:
            The event classes that currently have registered listeners.
        listener_count:
            The total number of registered event listeners.

    Methods:
        add_listener:
            Register an asynchronous listener for an event class.
        remove_listener:
            Remove a previously registered event listener.
        listen:
            Decorate and register an asynchronous event listener.
        listeners:
            Return the listeners registered for an event class.
        dispatch:
            Dispatch an event to every compatible listener.
        clear:
            Remove listeners for one event class or all event classes.
        __contains__:
            Determine whether an event class has registered listeners.
        __iter__:
            Iterate over registered event classes.
        __len__:
            Return the total number of registered listeners.
    """

    __slots__ = ("_listeners",)

    _listeners: dict[type[PlaybackEvent], list[_StoredEventListener]]

    def __init__(self) -> None:
        """Initialize an empty playback event dispatcher."""

        self._listeners = {}

    @property
    def event_types(self) -> tuple[type[PlaybackEvent], ...]:
        """Return event classes with registered listeners.

        Returns:
            The event classes in their registration order.
        """

        return tuple(self._listeners)

    @property
    def listener_count(self) -> int:
        """Return the total number of registered listeners.

        Returns:
            The number of listeners registered across all event classes.
        """

        return sum(len(listeners) for listeners in self._listeners.values())

    def add_listener[EventT: PlaybackEvent](self, event_type: type[EventT], listener: Callable[[EventT], Awaitable[None]]) -> Self:
        """Register an asynchronous listener for an event class.

        Registering the same listener more than once for the same event class
        has no effect.

        Args:
            event_type:
                The playback event class handled by the listener.
            listener:
                The asynchronous callable invoked when a matching event is
                dispatched.

        Returns:
            The dispatcher instance for chained listener registration.

        Raises:
            TypeError:
                The event type does not inherit from ``PlaybackEvent`` or the
                supplied listener is not callable.
        """

        self._validate_event_type(event_type)

        if not callable(listener):
            raise TypeError("The playback event listener must be a callable.")

        stored_listener: _StoredEventListener = cast(
            _StoredEventListener,
            listener
        )
        registered_listeners: list[_StoredEventListener] = (
            self._listeners.setdefault(event_type, [])
        )

        if stored_listener not in registered_listeners:
            registered_listeners.append(stored_listener)

        return self

    def remove_listener[EventT: PlaybackEvent](self, event_type: type[EventT], listener: Callable[[EventT], Awaitable[None]]) -> bool:
        """Remove a previously registered event listener.

        Args:
            event_type:
                The playback event class associated with the listener.
            listener:
                The asynchronous listener to remove.

        Returns:
            ``True`` when the listener was removed, otherwise ``False``.

        Raises:
            TypeError:
                The event type does not inherit from ``PlaybackEvent``.
        """

        self._validate_event_type(event_type)

        registered_listeners: list[_StoredEventListener] | None = (
            self._listeners.get(event_type)
        )

        if registered_listeners is None:
            return False

        stored_listener: _StoredEventListener = cast(
            _StoredEventListener,
            listener
        )

        try:
            registered_listeners.remove(stored_listener)
        except ValueError:
            return False

        if not registered_listeners:
            del self._listeners[event_type]

        return True

    def listen[EventT: PlaybackEvent](self, event_type: type[EventT]) -> Callable[
        [Callable[[EventT], Awaitable[None]]],
        Callable[[EventT], Awaitable[None]],
    ]:
        """Create a decorator that registers an event listener.

        Args:
            event_type:
                The playback event class handled by the decorated listener.

        Returns:
            A decorator that registers and returns the supplied listener.

        Raises:
            TypeError:
                The event type does not inherit from ``PlaybackEvent``.
        """

        self._validate_event_type(event_type)

        def decorator(listener: Callable[[EventT], Awaitable[None]]) -> Callable[[EventT], Awaitable[None]]:
            """Register and return the decorated listener."""

            self.add_listener(event_type, listener)
            return listener

        return decorator

    def listeners[EventT: PlaybackEvent](self,event_type: type[EventT]) -> tuple[Callable[[EventT], Awaitable[None]], ...]:
        """Return listeners registered directly for an event class.

        Listeners registered for compatible base event classes are not included
        in this result.

        Args:
            event_type:
                The playback event class whose listeners should be returned.

        Returns:
            The directly registered listeners in registration order.

        Raises:
            TypeError:
                The event type does not inherit from ``PlaybackEvent``.
        """

        self._validate_event_type(event_type)

        return cast(
            tuple[Callable[[EventT], Awaitable[None]], ...],
            tuple(self._listeners.get(event_type, ())),
        )

    async def dispatch(self, event: PlaybackEvent) -> None:
        """Dispatch a playback event to every compatible listener.

        Matching listeners are copied before execution so listeners may safely
        register or remove other listeners during event handling.

        Args:
            event:
                The playback event to dispatch.

        Raises:
            TypeError:
                The supplied value is not a playback event.
            ExceptionGroup:
                One or more listeners raised an exception.
        """

        if not isinstance(event, PlaybackEvent):
            raise TypeError("Only playback events can be dispatched.")

        matching_listeners: tuple[_StoredEventListener, ...] = tuple(
            listener
            for event_type, listeners in self._listeners.items()
            if isinstance(event, event_type)
            for listener in listeners
        )

        if not matching_listeners:
            return

        async with TaskGroup() as task_group:
            for listener in matching_listeners:
                task_group.create_task(listener(event))

    def clear(self, event_type: type[PlaybackEvent] | None = None) -> int:
        """Remove registered playback event listeners.

        Args:
            event_type:
                The event class whose listeners should be removed. Omitting the
                value removes every registered listener.

        Returns:
            The number of listeners removed.

        Raises:
            TypeError:
                The supplied event type does not inherit from
                ``PlaybackEvent``.
        """

        if event_type is None:
            removed_listener_count: int = self.listener_count
            self._listeners.clear()
            return removed_listener_count

        self._validate_event_type(event_type)

        removed_listeners: list[_StoredEventListener] | None = (self._listeners.pop(event_type, None))

        if removed_listeners is None:
            return 0

        return len(removed_listeners)

    def __contains__(self, event_type: object) -> bool:
        """Return whether an event class has registered listeners.

        Args:
            event_type:
                The possible playback event class to inspect.

        Returns:
            ``True`` when the event class has at least one listener.
        """

        if not isinstance(event_type, type):
            return False

        try:
            if not issubclass(event_type, PlaybackEvent):
                return False
        except TypeError:
            return False

        return bool(self._listeners.get(event_type))

    def __iter__(self) -> Iterator[type[PlaybackEvent]]:
        """Iterate over event classes with registered listeners.

        Returns:
            An iterator following event class registration order.
        """

        return iter(self._listeners)

    def __len__(self) -> int:
        """Return the total number of registered listeners.

        Returns:
            The number of listeners registered across all event classes.
        """

        return self.listener_count

    @staticmethod
    def _validate_event_type(event_type: type[PlaybackEvent]) -> None:
        """Validate a playback event class.

        Args:
            event_type:
                The possible playback event class to validate.

        Raises:
            TypeError:
                The value is not a class inheriting from ``PlaybackEvent``.
        """

        if not isinstance(event_type, type):
            raise TypeError("The playback event type must be a class.")

        try:
            valid_event_type: bool = issubclass(event_type, PlaybackEvent)
        except TypeError:
            valid_event_type = False

        if not valid_event_type:
            raise TypeError("The playback event type must inherit from PlaybackEvent.")

__all__: tuple[str, ...] = ("PlaybackEventDispatcher",)
"""Tests for the WumpiWave playback event dispatcher."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from wumpiwave.events.dispatcher import PlaybackEventDispatcher
from wumpiwave.models import PlaybackEvent


class ExamplePlaybackEvent(PlaybackEvent):
    """Represent a playback event used by dispatcher tests."""


class ChildPlaybackEvent(ExamplePlaybackEvent):
    """Represent a specialized playback event used by dispatcher tests."""


def create_event[
    EventT: PlaybackEvent
](
    event_type: type[EventT],
) -> EventT:
    """Create a mocked playback event with the requested runtime type."""

    return Mock(spec=event_type)

class PlaybackEventDispatcherTestCase(unittest.IsolatedAsyncioTestCase):
    """Test listener registration, removal, inspection, and dispatch."""

    def setUp(self) -> None:
        """Create an empty event dispatcher for each test."""

        self.dispatcher = PlaybackEventDispatcher()

    def test_creates_empty_dispatcher(self) -> None:
        """Verify that a new dispatcher contains no listeners."""

        self.assertEqual(self.dispatcher.event_types, ())
        self.assertEqual(self.dispatcher.listener_count, 0)
        self.assertEqual(len(self.dispatcher), 0)
        self.assertEqual(tuple(self.dispatcher), ())
        self.assertNotIn(ExamplePlaybackEvent, self.dispatcher)

    def test_add_listener_registers_listener(self) -> None:
        """Verify that an asynchronous listener can be registered."""

        async def listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        result = self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            listener
        )

        self.assertIs(result, self.dispatcher)
        self.assertEqual(
            self.dispatcher.listeners(ExamplePlaybackEvent),
            (listener,)
        )
        self.assertEqual(
            self.dispatcher.event_types,
            (ExamplePlaybackEvent,)
        )
        self.assertEqual(self.dispatcher.listener_count, 1)
        self.assertEqual(len(self.dispatcher), 1)
        self.assertIn(ExamplePlaybackEvent, self.dispatcher)

    def test_add_listener_ignores_duplicate_registration(self) -> None:
        """Verify that duplicate listener registration has no effect."""

        async def listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            listener
        )
        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            listener
        )

        self.assertEqual(
            self.dispatcher.listeners(ExamplePlaybackEvent),
            (listener,)
        )
        self.assertEqual(self.dispatcher.listener_count, 1)

    def test_add_listener_preserves_event_type_order(self) -> None:
        """Verify that event types retain registration order."""

        async def example_listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        async def child_listener(event: ChildPlaybackEvent) -> None:
            """Handle the child playback event."""

        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            example_listener
        )
        self.dispatcher.add_listener(
            ChildPlaybackEvent,
            child_listener
        )

        self.assertEqual(
            self.dispatcher.event_types,
            (
                ExamplePlaybackEvent,
                ChildPlaybackEvent
            )
        )
        self.assertEqual(
            tuple(self.dispatcher),
            (
                ExamplePlaybackEvent,
                ChildPlaybackEvent
            )
        )

    def test_add_listener_rejects_invalid_event_type(self) -> None:
        """Verify that event types must inherit from PlaybackEvent."""

        async def listener(event: object) -> None:
            """Handle an arbitrary object."""

        with self.assertRaises(TypeError):
            self.dispatcher.add_listener(
                object,  # type: ignore[arg-type]
                listener
            )

    def test_add_listener_rejects_non_class_event_type(self) -> None:
        """Verify that an event type must be a class."""

        async def listener(event: PlaybackEvent) -> None:
            """Handle a playback event."""

        with self.assertRaises(TypeError):
            self.dispatcher.add_listener(
                "PlaybackEvent",  # type: ignore[arg-type]
                listener
            )

    def test_add_listener_rejects_non_callable_listener(self) -> None:
        """Verify that registered listeners must be callable."""

        with self.assertRaises(TypeError):
            self.dispatcher.add_listener(
                ExamplePlaybackEvent,
                object() # type: ignore[arg-type]
            )

    def test_listen_decorator_registers_listener(self) -> None:
        """Verify that the decorator registers and returns its listener."""

        async def listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        decorated_listener = self.dispatcher.listen(ExamplePlaybackEvent)(listener)

        self.assertIs(decorated_listener, listener)
        self.assertEqual(
            self.dispatcher.listeners(ExamplePlaybackEvent),
            (listener,)
        )

    def test_listeners_returns_direct_listeners_only(self) -> None:
        """Verify that listener inspection excludes base event listeners."""

        async def base_listener(event: PlaybackEvent) -> None:
            """Handle every playback event."""

        async def child_listener(event: ChildPlaybackEvent) -> None:
            """Handle child playback events."""

        self.dispatcher.add_listener(
            PlaybackEvent,
            base_listener
        )
        self.dispatcher.add_listener(
            ChildPlaybackEvent,
            child_listener
        )

        self.assertEqual(
            self.dispatcher.listeners(ChildPlaybackEvent),
            (child_listener,)
        )

    def test_listeners_returns_empty_tuple_without_registration(self) -> None:
        """Verify that an unregistered event type has no listeners."""

        self.assertEqual(
            self.dispatcher.listeners(ExamplePlaybackEvent),
            ()
        )

    def test_remove_listener_returns_true_for_registration(self) -> None:
        """Verify that removing a registered listener returns true."""

        async def listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            listener
        )

        removed = self.dispatcher.remove_listener(
            ExamplePlaybackEvent,
            listener
        )

        self.assertTrue(removed)
        self.assertEqual(self.dispatcher.listener_count, 0)
        self.assertEqual(self.dispatcher.event_types, ())
        self.assertNotIn(ExamplePlaybackEvent, self.dispatcher)

    def test_remove_listener_returns_false_without_event_type(self) -> None:
        """Verify that removing from an unregistered type returns false."""

        async def listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        removed = self.dispatcher.remove_listener(
            ExamplePlaybackEvent,
            listener
        )

        self.assertFalse(removed)

    def test_remove_listener_returns_false_for_unknown_listener(self) -> None:
        """Verify that removing an unknown listener returns false."""

        async def registered_listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        async def unknown_listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            registered_listener
        )

        removed = self.dispatcher.remove_listener(
            ExamplePlaybackEvent,
            unknown_listener
        )

        self.assertFalse(removed)
        self.assertEqual(
            self.dispatcher.listeners(ExamplePlaybackEvent),
            (registered_listener,)
        )

    async def test_dispatch_invokes_registered_listener(self) -> None:
        """Verify that dispatch invokes a matching listener."""

        received_events: list[PlaybackEvent] = []

        async def listener(event: ExamplePlaybackEvent) -> None:
            """Record the dispatched playback event."""

            received_events.append(event)

        event = create_event(ExamplePlaybackEvent)

        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            listener
        )
        await self.dispatcher.dispatch(event)

        self.assertEqual(received_events, [event])

    async def test_dispatch_invokes_compatible_base_listeners(self) -> None:
        """Verify that child events invoke compatible base listeners."""

        received_by: set[str] = set()

        async def base_listener(event: PlaybackEvent) -> None:
            """Record invocation of the base listener."""

            received_by.add("base")

        async def example_listener(event: ExamplePlaybackEvent) -> None:
            """Record invocation of the example listener."""

            received_by.add("example")

        async def child_listener(event: ChildPlaybackEvent) -> None:
            """Record invocation of the child listener."""

            received_by.add("child")

        self.dispatcher.add_listener(
            PlaybackEvent,
            base_listener
        )
        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            example_listener
        )
        self.dispatcher.add_listener(
            ChildPlaybackEvent,
            child_listener
        )

        await self.dispatcher.dispatch(create_event(ChildPlaybackEvent))

        self.assertEqual(
            received_by,
            {
                "base",
                "example",
                "child"
            }
        )

    async def test_dispatch_does_not_invoke_child_listener_for_base_event(self) -> None:
        """Verify that base events do not invoke specialized listeners."""

        calls: list[str] = []

        async def base_listener(event: PlaybackEvent) -> None:
            """Record invocation of the base listener."""

            calls.append("base")

        async def child_listener(event: ChildPlaybackEvent) -> None:
            """Record invocation of the child listener."""

            calls.append("child")

        self.dispatcher.add_listener(
            PlaybackEvent,
            base_listener
        )
        self.dispatcher.add_listener(
            ChildPlaybackEvent,
            child_listener
        )

        await self.dispatcher.dispatch(create_event(ExamplePlaybackEvent))

        self.assertEqual(calls, ["base"])

    async def test_dispatch_without_matching_listener_returns(self) -> None:
        """Verify that dispatching without listeners completes normally."""

        await self.dispatcher.dispatch(create_event(ExamplePlaybackEvent))

    async def test_dispatch_rejects_non_playback_event(self) -> None:
        """Verify that only playback events can be dispatched."""

        with self.assertRaises(TypeError):
            await self.dispatcher.dispatch(object())  # type: ignore[arg-type]

    async def test_listener_exception_is_propagated(self) -> None:
        """Verify that listener failures produce an exception group."""

        async def failing_listener( event: ExamplePlaybackEvent) -> None:
            """Raise an example listener failure."""

            raise RuntimeError("Listener failed.")

        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            failing_listener
        )

        with self.assertRaises(ExceptionGroup):
            await self.dispatcher.dispatch(create_event(ExamplePlaybackEvent))

    async def test_dispatch_uses_listener_snapshot(self) -> None:
        """Verify that removal during dispatch does not skip listeners."""

        calls: set[str] = set()

        async def first_listener(event: ExamplePlaybackEvent) -> None:
            """Remove another listener during dispatch."""

            calls.add("first")
            self.dispatcher.remove_listener(
                ExamplePlaybackEvent,
                second_listener
            )

        async def second_listener(event: ExamplePlaybackEvent) -> None:
            """Record invocation of the second listener."""

            calls.add("second")

        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            first_listener
        )
        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            second_listener
        )

        await self.dispatcher.dispatch(create_event(ExamplePlaybackEvent))

        self.assertEqual(
            calls,
            {
                "first",
                "second"
            }
        )
        self.assertEqual(
            self.dispatcher.listeners(ExamplePlaybackEvent),
            (first_listener,)
        )

    def test_clear_removes_listeners_for_event_type(self) -> None:
        """Verify that one event type can be cleared independently."""

        async def example_listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        async def child_listener(event: ChildPlaybackEvent) -> None:
            """Handle the child playback event."""

        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            example_listener
        )
        self.dispatcher.add_listener(
            ChildPlaybackEvent,
            child_listener
        )

        removed_count = self.dispatcher.clear(ExamplePlaybackEvent)

        self.assertEqual(removed_count, 1)
        self.assertEqual(
            self.dispatcher.event_types,
            (ChildPlaybackEvent,)
        )
        self.assertEqual(self.dispatcher.listener_count, 1)

    def test_clear_returns_zero_for_unregistered_event_type(self) -> None:
        """Verify that clearing an unknown event type returns zero."""

        removed_count = self.dispatcher.clear(
            ExamplePlaybackEvent
        )

        self.assertEqual(removed_count, 0)

    def test_clear_without_event_type_removes_every_listener(self) -> None:
        """Verify that all listeners can be removed together."""

        async def first_listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        async def second_listener(event: ExamplePlaybackEvent) -> None:
            """Handle the example playback event."""

        async def child_listener(event: ChildPlaybackEvent) -> None:
            """Handle the child playback event."""

        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            first_listener
        )
        self.dispatcher.add_listener(
            ExamplePlaybackEvent,
            second_listener
        )
        self.dispatcher.add_listener(
            ChildPlaybackEvent,
            child_listener
        )

        removed_count = self.dispatcher.clear()

        self.assertEqual(removed_count, 3)
        self.assertEqual(self.dispatcher.event_types, ())
        self.assertEqual(self.dispatcher.listener_count, 0)
        self.assertEqual(len(self.dispatcher), 0)

if __name__ == "__main__":
    unittest.main()
"""Asyncio-based event loop for runtui."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Callable

from ..backend.base import Backend
from .event import Event, EventDispatcher, MouseEvent, ResizeEvent, Strategy
from .timer import TimerHandle, TimerManager

if TYPE_CHECKING:
    pass


class EventLoop:
    """Main event loop: reads input, dispatches events, triggers paint/flush."""

    def __init__(self, backend: Backend) -> None:
        self._backend = backend
        self._dispatcher = EventDispatcher()
        self._timers = TimerManager()
        self._running = False
        self._app: Any = None
        self._idle_callbacks: list[Callable[[], None]] = []
        self._pending_events: list[Event] = []
        self._frame_rate = 60
        self._frame_interval = 1.0 / self._frame_rate

    @property
    def dispatcher(self) -> EventDispatcher:
        return self._dispatcher

    @property
    def timers(self) -> TimerManager:
        return self._timers

    def call_later(self, delay: float, callback: Callable[[], None]) -> TimerHandle:
        return self._timers.call_later(delay, callback)

    def set_interval(self, interval: float, callback: Callable[[], None]) -> TimerHandle:
        return self._timers.set_interval(interval, callback)

    def call_soon(self, callback: Callable[[], None]) -> None:
        self._idle_callbacks.append(callback)

    def post_event(self, event: Event) -> None:
        self._pending_events.append(event)

    def stop(self) -> None:
        self._running = False

    async def run(self, app: Any) -> None:
        """Main loop."""
        self._app = app
        self._running = True

        while self._running:
            frame_start = time.monotonic()

            # 1. Read raw terminal input
            raw = self._backend.read_input()

            # 2. Decode into events
            events = self._backend.decode_input(raw) if raw else []

            # Add any pending programmatic events
            if self._pending_events:
                events.extend(self._pending_events)
                self._pending_events.clear()

            # 3. Dispatch each event
            for event in events:
                if isinstance(event, ResizeEvent):
                    app._handle_resize(event)
                elif isinstance(event, MouseEvent):
                    app._handle_mouse(event)
                else:
                    app._handle_event(event)

            # 4. Process timers
            self._timers.process()

            # 5. Process idle callbacks
            if self._idle_callbacks:
                callbacks = self._idle_callbacks[:]
                self._idle_callbacks.clear()
                for cb in callbacks:
                    cb()

            # 6. Paint + flush (app handles skip-if-clean internally)
            app._paint()
            app._flush()

            # Frame rate limiting
            elapsed = time.monotonic() - frame_start
            sleep_time = self._frame_interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(0)

"""Timer and interval support for the event loop."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class TimerHandle:
    """Handle to a scheduled timer. Can be cancelled."""
    callback: Callable[[], None]
    fire_at: float
    interval: float = 0.0  # 0 = one-shot, >0 = repeating
    cancelled: bool = False
    _id: int = 0

    def cancel(self) -> None:
        self.cancelled = True


_next_timer_id = 0


def _new_timer_id() -> int:
    global _next_timer_id
    _next_timer_id += 1
    return _next_timer_id


class TimerManager:
    """Manages timers and intervals."""

    def __init__(self) -> None:
        self._timers: list[TimerHandle] = []

    def call_later(self, delay: float, callback: Callable[[], None]) -> TimerHandle:
        handle = TimerHandle(
            callback=callback,
            fire_at=time.monotonic() + delay,
            _id=_new_timer_id(),
        )
        self._timers.append(handle)
        return handle

    def set_interval(self, interval: float, callback: Callable[[], None]) -> TimerHandle:
        handle = TimerHandle(
            callback=callback,
            fire_at=time.monotonic() + interval,
            interval=interval,
            _id=_new_timer_id(),
        )
        self._timers.append(handle)
        return handle

    def process(self) -> None:
        """Fire any timers that are due. Called from the event loop."""
        now = time.monotonic()
        fired: list[TimerHandle] = []

        for handle in self._timers:
            if handle.cancelled:
                fired.append(handle)
                continue
            if now >= handle.fire_at:
                handle.callback()
                if handle.interval > 0:
                    handle.fire_at = now + handle.interval
                else:
                    fired.append(handle)

        for handle in fired:
            if handle in self._timers:
                self._timers.remove(handle)

    def cancel_all(self) -> None:
        for handle in self._timers:
            handle.cancelled = True
        self._timers.clear()

    @property
    def next_deadline(self) -> float | None:
        """Return time until next timer fires, or None if no timers."""
        if not self._timers:
            return None
        active = [h for h in self._timers if not h.cancelled]
        if not active:
            return None
        now = time.monotonic()
        return max(0.0, min(h.fire_at for h in active) - now)

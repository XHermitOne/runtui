"""Event base classes, typed events, and dispatch system."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from .keys import Keys, Modifiers, MouseAction, MouseButton

if TYPE_CHECKING:
    from ..widgets.base import Widget


class Phase(enum.Enum):
    TUNNEL = "tunnel"
    BUBBLE = "bubble"


class Strategy(enum.Enum):
    TUNNEL_THEN_BUBBLE = "tunnel_then_bubble"
    DIRECT = "direct"
    BROADCAST = "broadcast"


# --- Event Hierarchy ---

@dataclass
class Event:
    """Base for all events."""
    timestamp: float = field(default_factory=time.monotonic)
    handled: bool = False
    cancelled: bool = False
    _propagation_stopped: bool = field(default=False, repr=False)

    def stop_propagation(self) -> None:
        self._propagation_stopped = True

    def prevent_default(self) -> None:
        self.cancelled = True

    def mark_handled(self) -> None:
        self.handled = True
        self.stop_propagation()


class InputEvent(Event):
    """Base for user-input events (keyboard, mouse)."""
    pass


@dataclass
class KeyEvent(InputEvent):
    key: Keys = Keys.UNKNOWN
    char: str = ""
    modifiers: Modifiers = Modifiers.NONE
    is_repeat: bool = False


@dataclass
class MouseEvent(InputEvent):
    x: int = 0
    y: int = 0
    button: MouseButton = MouseButton.NONE
    action: MouseAction = MouseAction.MOVE
    modifiers: Modifiers = Modifiers.NONE


@dataclass
class FocusEvent(Event):
    gained: bool = True
    previous: Any = None  # Widget reference
    next: Any = None


class WindowAction(enum.Enum):
    CLOSE = "close"
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    RESTORE = "restore"
    MOVE = "move"
    RESIZE = "resize"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"


@dataclass
class WindowEvent(Event):
    action: WindowAction = WindowAction.CLOSE
    window: Any = None


@dataclass
class ResizeEvent(Event):
    width: int = 0
    height: int = 0


@dataclass
class ThemeChangedEvent(Event):
    theme_name: str = ""


@dataclass
class CustomEvent(Event):
    name: str = ""
    data: Any = None


# --- Subscription ---

@dataclass
class Subscription:
    """Handle for removing an event handler."""
    _owner: Any = None
    _event_type: type[Event] | None = None
    _handler: Callable | None = None
    _phase: Phase = Phase.BUBBLE
    _disposed: bool = False

    def dispose(self) -> None:
        if not self._disposed and self._owner is not None:
            self._owner._remove_handler(self._event_type, self._handler, self._phase)
            self._disposed = True


# --- Handler Storage ---

@dataclass
class _HandlerEntry:
    event_type: type[Event]
    handler: Callable
    phase: Phase
    once: bool = False


class EventMixin:
    """Mixin that provides event handler registration to any class."""

    def __init_event_mixin__(self) -> None:
        self._handlers: list[_HandlerEntry] = []

    def on(
        self,
        event_type: type[Event],
        handler: Callable[[Event], None],
        phase: Phase = Phase.BUBBLE,
    ) -> Subscription:
        entry = _HandlerEntry(event_type, handler, phase)
        self._handlers.append(entry)
        return Subscription(
            _owner=self,
            _event_type=event_type,
            _handler=handler,
            _phase=phase,
        )

    def once(
        self,
        event_type: type[Event],
        handler: Callable[[Event], None],
        phase: Phase = Phase.BUBBLE,
    ) -> Subscription:
        entry = _HandlerEntry(event_type, handler, phase, once=True)
        self._handlers.append(entry)
        return Subscription(
            _owner=self,
            _event_type=event_type,
            _handler=handler,
            _phase=phase,
        )

    def emit(self, event: Event) -> None:
        """Emit an event, dispatching to local handlers (bubble phase)."""
        self._invoke_handlers(event, Phase.BUBBLE)

    def _invoke_handlers(self, event: Event, phase: Phase) -> None:
        to_remove: list[_HandlerEntry] = []
        for entry in self._handlers:
            if event._propagation_stopped:
                break
            if isinstance(event, entry.event_type) and entry.phase == phase:
                entry.handler(event)
                if entry.once:
                    to_remove.append(entry)
        for entry in to_remove:
            self._handlers.remove(entry)

    def _remove_handler(
        self, event_type: type[Event] | None, handler: Callable | None, phase: Phase
    ) -> None:
        self._handlers = [
            e
            for e in self._handlers
            if not (e.event_type == event_type and e.handler == handler and e.phase == phase)
        ]


# --- Event Dispatcher ---

class EventDispatcher:
    """Routes events through the widget tree using tunnel/bubble strategy."""

    def dispatch(self, event: Event, target: Any, strategy: Strategy = Strategy.TUNNEL_THEN_BUBBLE) -> None:
        if target is None:
            return

        if strategy == Strategy.DIRECT:
            target._invoke_handlers(event, Phase.BUBBLE)
            return

        if strategy == Strategy.BROADCAST:
            self._broadcast(event, target)
            return

        # TUNNEL_THEN_BUBBLE
        path = self._build_path(target)

        # Tunnel phase (root -> target)
        for widget in path:
            if event._propagation_stopped:
                return
            widget._invoke_handlers(event, Phase.TUNNEL)

        # Bubble phase (target -> root)
        for widget in reversed(path):
            if event._propagation_stopped:
                return
            widget._invoke_handlers(event, Phase.BUBBLE)

    def _build_path(self, target: Any) -> list[Any]:
        path: list[Any] = []
        current = target
        while current is not None:
            path.append(current)
            current = getattr(current, "parent", None)
        path.reverse()
        return path

    def _broadcast(self, event: Event, root: Any) -> None:
        root._invoke_handlers(event, Phase.BUBBLE)
        for child in getattr(root, "children", []):
            if event._propagation_stopped:
                return
            self._broadcast(event, child)

"""Base Widget class -- foundation for all UI elements."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..core.event import Event, EventMixin, FocusEvent, Phase, Subscription
from ..core.types import Attrs, Color, Point, Rect, Size
from ..rendering.painter import Painter

if TYPE_CHECKING:
    from ..layout.base import LayoutManager
    from ..themes.engine import ThemeEngine


class Widget(EventMixin):
    """Base class for all TUI widgets."""

    def __init__(
        self,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 0,
    ) -> None:
        self.__init_event_mixin__()

        # Identity
        self.id = id
        self.classes: set[str] = set()

        # Tree
        self.parent: Widget | None = None
        self.children: list[Widget] = []

        # Geometry (relative to parent)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_width = 0
        self.min_height = 0
        self.max_width = 9999
        self.max_height = 9999

        # Layout hints
        self.dock: str = ""  # "top", "bottom", "left", "right", "fill"
        self.flex: float = 0.0  # For box layouts

        # State
        self.visible = True
        self.enabled = True
        self._focused = False
        self.can_focus = False
        self._needs_layout = True
        self._needs_paint = True

        # Layout manager (for containers)
        self._layout_manager: LayoutManager | None = None

        # Screen rect (absolute position, computed during layout)
        self._screen_rect = Rect(0, 0, 0, 0)

    @property
    def focused(self) -> bool:
        return self._focused

    @property
    def screen_rect(self) -> Rect:
        return self._screen_rect

    @property
    def content_rect(self) -> Rect:
        """Rect for content area (inside any borders/padding)."""
        return self._screen_rect

    # --- Tree Operations ---

    def add_child(self, child: Widget) -> None:
        if child.parent is not None:
            child.parent.remove_child(child)
        child.parent = self
        self.children.append(child)
        self.invalidate_layout()

    def remove_child(self, child: Widget) -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            self.invalidate_layout()

    def clear_children(self) -> None:
        for child in self.children[:]:
            child.parent = None
        self.children.clear()
        self.invalidate_layout()

    def find_by_id(self, widget_id: str) -> Widget | None:
        if self.id == widget_id:
            return self
        for child in self.children:
            found = child.find_by_id(widget_id)
            if found:
                return found
        return None

    def ancestors(self) -> list[Widget]:
        result: list[Widget] = []
        current = self.parent
        while current is not None:
            result.append(current)
            current = current.parent
        return result

    def root(self) -> Widget:
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    # --- Layout ---

    def measure(self, available: Size) -> Size:
        """Return desired size given available space. Override in subclasses."""
        w = min(self.width or available.width, self.max_width)
        h = min(self.height or available.height, self.max_height)
        w = max(w, self.min_width)
        h = max(h, self.min_height)
        return Size(w, h)

    def arrange(self, rect: Rect) -> None:
        """Position this widget within the given rect. Override in containers."""
        self._screen_rect = rect
        self.x = rect.x
        self.y = rect.y
        self.width = rect.width
        self.height = rect.height
        if self._layout_manager and self.children:
            self._layout_manager.arrange(self, rect)
        self._needs_layout = False

    def layout_if_needed(self) -> None:
        """Recursively layout if dirty."""
        if self._needs_layout:
            self.arrange(self._screen_rect)
        for child in self.children:
            if child.visible:
                child.layout_if_needed()

    def invalidate(self) -> None:
        """Mark for repaint."""
        self._needs_paint = True

    def invalidate_layout(self) -> None:
        """Mark for re-layout and repaint."""
        self._needs_layout = True
        self._needs_paint = True
        if self.parent:
            self.parent.invalidate_layout()

    # --- Painting ---

    def paint(self, painter: Painter) -> None:
        """Draw this widget. Override in subclasses."""
        pass

    def paint_if_needed(self, painter: Painter) -> None:
        """Recursively paint if dirty."""
        if not self.visible:
            return
        if self._needs_paint:
            self.paint(painter)
            self._needs_paint = False
        for child in self.children:
            child.paint_if_needed(painter)

    def get_painter(self, parent_painter: Painter) -> Painter:
        """Get a painter clipped to this widget's area."""
        return parent_painter.sub_painter(
            self._screen_rect.x - parent_painter._offset.x,
            self._screen_rect.y - parent_painter._offset.y,
            self._screen_rect.width,
            self._screen_rect.height,
        )

    # --- Focus ---

    def focus(self) -> None:
        if not self.can_focus or not self.enabled:
            return
        # Blur previously focused widget in the same window subtree.
        # Walk up to the nearest Window (or root if no window found)
        # so that focus correctly transfers between siblings.
        scope = self._focus_scope()
        current_focused = _find_focused(scope)
        if current_focused is self:
            return
        if current_focused:
            current_focused._set_focused(False)
        self._set_focused(True)

    def _focus_scope(self) -> Widget:
        """Return the nearest ancestor that acts as a focus scope.

        Windows and Dialogs serve as focus scopes so that focus changes
        stay within the same window.  Falls back to root() if no scope
        is found.
        """
        from ..windows.window import Window
        from ..dialogs.base import Dialog
        current: Widget | None = self
        while current is not None:
            if isinstance(current, (Window, Dialog)):
                return current
            current = current.parent
        return self.root()

    def blur(self) -> None:
        self._set_focused(False)

    def _set_focused(self, value: bool) -> None:
        if self._focused == value:
            return
        self._focused = value
        self.invalidate()
        event = FocusEvent(gained=value)
        self.emit(event)

    def focus_next(self) -> Widget | None:
        """Move focus to next focusable widget. Returns the newly focused widget."""
        focusable = _collect_focusable(self._focus_scope())
        if not focusable:
            return None
        try:
            idx = focusable.index(self)
            next_idx = (idx + 1) % len(focusable)
        except ValueError:
            next_idx = 0
        focusable[next_idx].focus()
        return focusable[next_idx]

    def focus_prev(self) -> Widget | None:
        """Move focus to previous focusable widget."""
        focusable = _collect_focusable(self._focus_scope())
        if not focusable:
            return None
        try:
            idx = focusable.index(self)
            prev_idx = (idx - 1) % len(focusable)
        except ValueError:
            prev_idx = len(focusable) - 1
        focusable[prev_idx].focus()
        return focusable[prev_idx]

    # --- Hit Testing ---

    def hit_test(self, x: int, y: int) -> Widget | None:
        """Return deepest widget at screen coords (x, y)."""
        if not self.visible or not self._screen_rect.contains(x, y):
            return None
        # Check children in reverse (top-most first)
        for child in reversed(self.children):
            hit = child.hit_test(x, y)
            if hit is not None:
                return hit
        return self

    # --- Theme ---

    def get_theme(self) -> ThemeEngine | None:
        """Walk up tree to find the theme engine."""
        current: Widget | None = self
        while current is not None:
            engine = getattr(current, "_theme_engine", None)
            if engine is not None:
                return engine
            current = current.parent
        return None

    def theme_color(self, slot: str, fallback: Color = Color.DEFAULT) -> Color:
        """Get a color from the current theme."""
        engine = self.get_theme()
        if engine:
            return engine.get_color(slot, fallback)
        return fallback

    def theme_glyph(self, slot: str, fallback: str = "") -> str:
        """Get a glyph from the current theme."""
        engine = self.get_theme()
        if engine:
            return engine.get_glyph(slot, fallback)
        return fallback

    def __repr__(self) -> str:
        name = self.__class__.__name__
        id_str = f" id={self.id!r}" if self.id else ""
        return f"<{name}{id_str} ({self.x},{self.y} {self.width}x{self.height})>"


def _find_focused(widget: Widget) -> Widget | None:
    """Find the currently focused widget in the tree."""
    if widget._focused:
        return widget
    for child in widget.children:
        found = _find_focused(child)
        if found:
            return found
    return None


def _collect_focusable(root: Widget) -> list[Widget]:
    """Collect all focusable widgets in depth-first order."""
    result: list[Widget] = []
    if root.can_focus and root.visible and root.enabled:
        result.append(root)
    for child in root.children:
        result.extend(_collect_focusable(child))
    return result

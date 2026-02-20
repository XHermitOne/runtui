"""Window manager -- z-order, focus, tiling, cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.event import MouseEvent, WindowAction, WindowEvent
from ..core.keys import MouseAction as MA, MouseButton
from ..core.types import Rect
from ..rendering.painter import Painter
from ..widgets.base import Widget
from .window import Window, WindowState

if TYPE_CHECKING:
    pass


class WindowManager:
    """Manages multiple windows: z-order, focus, move, minimize/maximize/close."""

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self._windows: list[Window] = []  # z-order: 0=bottom
        self._active: Window | None = None
        self._screen_width = screen_width
        self._screen_height = screen_height
        self._taskbar_height = 1
        self._menu_height = 1
        self._next_cascade_x = 2
        self._next_cascade_y = 2

    @property
    def windows(self) -> list[Window]:
        return list(self._windows)

    @property
    def visible_windows(self) -> list[Window]:
        return [w for w in self._windows if w.visible]

    @property
    def active_window(self) -> Window | None:
        return self._active

    @property
    def desktop_rect(self) -> Rect:
        """Available area for windows (between menu and taskbar)."""
        return Rect(
            0,
            self._menu_height,
            self._screen_width,
            self._screen_height - self._menu_height - self._taskbar_height,
        )

    def resize_screen(self, width: int, height: int) -> None:
        self._screen_width = width
        self._screen_height = height
        # Update screen bounds on all windows
        bounds = (width, height - self._taskbar_height)
        for win in self._windows:
            win._screen_bounds = bounds
        # Re-maximize any maximized windows
        for win in self._windows:
            if win.state == WindowState.MAXIMIZED:
                dr = self.desktop_rect
                win.x = dr.x
                win.y = dr.y
                win.width = dr.width
                win.height = dr.height
                win._screen_rect = Rect(dr.x, dr.y, dr.width, dr.height)
                win.invalidate_layout()

    def add_window(self, window: Window, activate: bool = True) -> None:
        """Add a window. Cascades position if at defaults."""
        if window in self._windows:
            return

        # Auto-cascade position
        if window.x <= 2 and window.y <= 1:
            window.x = self._next_cascade_x
            window.y = self._next_cascade_y
            self._next_cascade_x += 2
            self._next_cascade_y += 1
            dr = self.desktop_rect
            if self._next_cascade_x > dr.width // 3:
                self._next_cascade_x = 2
            if self._next_cascade_y > dr.height // 3:
                self._next_cascade_y = 2

        window._screen_rect = Rect(window.x, window.y, window.width, window.height)
        window._screen_bounds = (self._screen_width, self._screen_height - self._taskbar_height)
        self._windows.append(window)

        # Listen for window events
        window.on(WindowEvent, lambda e: self._on_window_event(e))

        if activate:
            self.activate(window)

    def remove_window(self, window: Window) -> None:
        if window in self._windows:
            self._windows.remove(window)
            if self._active is window:
                self._active = None
                # Activate next top window
                visible = self.visible_windows
                if visible:
                    self.activate(visible[-1])

    def activate(self, window: Window) -> None:
        """Bring window to front and give it focus."""
        if window not in self._windows or not window.visible:
            return
        if self._active is not None and self._active is not window:
            self._active.is_active = False
            self._active.emit(WindowEvent(action=WindowAction.DEACTIVATE, window=self._active))
        window.is_active = True
        # Move to top of z-order
        if window in self._windows:
            self._windows.remove(window)
            self._windows.append(window)
        self._active = window
        window.emit(WindowEvent(action=WindowAction.ACTIVATE, window=window))

    def bring_to_front(self, window: Window) -> None:
        self.activate(window)

    def minimize(self, window: Window) -> None:
        window._do_minimize()

    def maximize(self, window: Window) -> None:
        dr = self.desktop_rect
        window._restore_rect = Rect(window.x, window.y, window.width, window.height)
        window._state = WindowState.MAXIMIZED
        window.x = dr.x
        window.y = dr.y
        window.width = dr.width
        window.height = dr.height
        window._screen_rect = Rect(dr.x, dr.y, dr.width, dr.height)
        window.invalidate_layout()
        window.emit(WindowEvent(action=WindowAction.MAXIMIZE, window=window))

    def restore(self, window: Window) -> None:
        window.restore()

    def close(self, window: Window) -> None:
        window._do_close()
        self.remove_window(window)

    def cycle_next(self) -> None:
        """Cycle to next window (Alt+Tab behavior)."""
        visible = self.visible_windows
        if len(visible) < 2:
            return
        if self._active in visible:
            idx = visible.index(self._active)
            next_win = visible[(idx + 1) % len(visible)]
        else:
            next_win = visible[0]
        self.activate(next_win)

    def cycle_prev(self) -> None:
        visible = self.visible_windows
        if len(visible) < 2:
            return
        if self._active in visible:
            idx = visible.index(self._active)
            prev_win = visible[(idx - 1) % len(visible)]
        else:
            prev_win = visible[-1]
        self.activate(prev_win)

    def cascade(self) -> None:
        """Arrange windows in a cascade pattern."""
        dr = self.desktop_rect
        x, y = dr.x + 1, dr.y + 1
        for win in self._windows:
            if not win.visible:
                continue
            win._state = WindowState.NORMAL
            w = min(dr.width - 4, win.width)
            h = min(dr.height - 4, win.height)
            win.x = x
            win.y = y
            win.width = w
            win.height = h
            win._screen_rect = Rect(x, y, w, h)
            win.invalidate_layout()
            x += 2
            y += 1
            if x > dr.width // 2:
                x = dr.x + 1
            if y > dr.height // 2:
                y = dr.y + 1

    def tile_horizontal(self) -> None:
        """Tile windows side by side."""
        visible = self.visible_windows
        if not visible:
            return
        dr = self.desktop_rect
        w = dr.width // len(visible)
        for i, win in enumerate(visible):
            win.x = dr.x + i * w
            win.y = dr.y
            win.width = w
            win.height = dr.height
            win._state = WindowState.NORMAL
            win._screen_rect = Rect(win.x, win.y, win.width, win.height)
            win.invalidate_layout()

    def tile_vertical(self) -> None:
        """Tile windows stacked vertically."""
        visible = self.visible_windows
        if not visible:
            return
        dr = self.desktop_rect
        h = dr.height // len(visible)
        for i, win in enumerate(visible):
            win.x = dr.x
            win.y = dr.y + i * h
            win.width = dr.width
            win.height = h
            win._state = WindowState.NORMAL
            win._screen_rect = Rect(win.x, win.y, win.width, win.height)
            win.invalidate_layout()

    def hit_test(self, x: int, y: int) -> Window | None:
        """Find topmost window at screen position."""
        for win in reversed(self._windows):
            if win.visible and win._screen_rect.contains(x, y):
                return win
        return None

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Route mouse event to appropriate window. Returns True if handled."""
        win = self.hit_test(event.x, event.y)
        if win is not None:
            if event.action == MA.PRESS and event.button == MouseButton.LEFT:
                if win is not self._active:
                    self.activate(win)
            return True
        return False

    def paint(self, painter: Painter) -> None:
        """Paint all visible windows in z-order."""
        self._overlay_widgets = []
        for win in self._windows:
            if win.visible:
                # Ensure layout is up to date
                win.arrange(win._screen_rect)
                # Paint window chrome
                win.paint(painter)
                # Paint window content and children unconditionally
                # since the back buffer is cleared each frame
                self._paint_children(painter, win)

        # Paint dropdown overlays on top of all window content
        self._paint_overlays(painter)

    def _paint_children(self, painter: Painter, widget: Widget) -> None:
        """Recursively paint all visible children unconditionally."""
        for child in widget.children:
            if child.visible:
                child.paint(painter)
                child._needs_paint = False
                # Collect expanded dropdowns for overlay painting
                if hasattr(child, '_expanded') and child._expanded and hasattr(child, '_paint_dropdown'):
                    self._overlay_widgets.append(child)
                self._paint_children(painter, child)

    def _paint_overlays(self, painter: Painter) -> None:
        """Paint dropdown overlays on top of all window content."""
        for widget in self._overlay_widgets:
            sr = widget._screen_rect
            lx = sr.x - painter._offset.x
            ly = sr.y - painter._offset.y
            widget._paint_dropdown(painter, lx, ly + 1, sr.width)

    def _on_window_event(self, event: WindowEvent) -> None:
        if event.action == WindowAction.CLOSE:
            self.remove_window(event.window)
        elif event.action == WindowAction.MAXIMIZE:
            dr = self.desktop_rect
            w = event.window
            w.x = dr.x
            w.y = dr.y
            w.width = dr.width
            w.height = dr.height
            w._screen_rect = Rect(dr.x, dr.y, dr.width, dr.height)
            w.invalidate_layout()
        elif event.action == WindowAction.MINIMIZE:
            if self._active is event.window:
                # Activate next window
                visible = self.visible_windows
                if visible:
                    self.activate(visible[-1])
                else:
                    self._active = None

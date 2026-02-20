"""Application class -- main entry point for runtui applications."""

from __future__ import annotations

import asyncio
import sys
from typing import Any, Callable

from .backend.base import Backend
from .backend.detect import create_backend
from .core.event import (
    Event,
    EventDispatcher,
    KeyEvent,
    MouseEvent,
    ResizeEvent,
    Strategy,
    ThemeChangedEvent,
    WindowEvent,
    WindowAction,
    Phase,
)
from .core.event_loop import EventLoop
from .core.keys import Keys, Modifiers, MouseAction as MA, MouseButton
from .core.timer import TimerHandle
from .core.types import Color, Rect, Size
from .layout.dock import DockLayout
from .mouse.cursor import MouseCursor
from .mouse.tracker import MouseTracker
from .rendering.buffer import CellBuffer
from .rendering.painter import Painter
from .rendering.screen import Screen
from .themes.engine import ThemeEngine, ThemeDefinition
from .themes.turbo_vision import turbo_vision_theme
from .widgets.base import Widget, _find_focused
from .widgets.container import Container
from .widgets.label import Label
from .windows.taskbar import TaskBar
from .windows.window import Window
from .windows.window_manager import WindowManager


class Desktop(Widget):
    """Desktop background widget -- fills with a pattern."""

    def __init__(self) -> None:
        super().__init__()
        self.can_focus = False

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        bg = self.theme_color("desktop.bg", Color.BLUE)
        fg = self.theme_color("desktop.fg", Color.CYAN)
        for row in range(sr.height):
            for col in range(sr.width):
                ch = "░" if (row + col) % 2 == 0 else " "
                painter.put_char(
                    col + sr.x - painter._offset.x,
                    row + sr.y - painter._offset.y,
                    ch, fg=fg, bg=bg,
                )


class App:
    """Main application class. Subclass this to create a runtui application."""

    def __init__(self, theme: str = "turbo_vision") -> None:
        self._backend: Backend | None = None
        self._screen: Screen | None = None
        self._event_loop: EventLoop | None = None
        self._theme_engine = ThemeEngine()
        self._mouse_cursor = MouseCursor()
        self._mouse_tracker = MouseTracker()
        self._window_manager: WindowManager | None = None
        self._taskbar: TaskBar | None = None
        self._menu_bar: Widget | None = None
        self._desktop: Desktop | None = None
        self._initial_theme = theme
        self.running = False
        self._needs_repaint = True

        # Root container (holds desktop + taskbar, NOT windows)
        self.root: Widget | None = None

        # Mouse capture: when dragging/resizing, all mouse events go to this widget
        self._mouse_capture: Widget | None = None

        # Register built-in themes
        self._register_builtin_themes()

    def _register_builtin_themes(self) -> None:
        self._theme_engine.register(turbo_vision_theme)

        try:
            from .themes.github import github_theme
            self._theme_engine.register(github_theme)
        except ImportError:
            pass
        try:
            from .themes.vscode import vscode_theme
            self._theme_engine.register(vscode_theme)
        except ImportError:
            pass
        try:
            from .themes.gruvbox import gruvbox_theme
            self._theme_engine.register(gruvbox_theme)
        except ImportError:
            pass
        try:
            from .themes.high_contrast import high_contrast_theme
            self._theme_engine.register(high_contrast_theme)
        except ImportError:
            pass
        try:
            from .themes.legacy_system import legacy_system_theme
            self._theme_engine.register(legacy_system_theme)
        except ImportError:
            pass
        try:
            from .themes.black_white import black_white_theme
            self._theme_engine.register(black_white_theme)
        except ImportError:
            pass
        try:
            from .themes.dark import dark_theme
            self._theme_engine.register(dark_theme)
        except ImportError:
            pass
        try:
            from .themes.light import light_theme
            self._theme_engine.register(light_theme)
        except ImportError:
            pass
        try:
            from .themes.nord import nord_theme
            self._theme_engine.register(nord_theme)
        except ImportError:
            pass
        try:
            from .themes.solarized import solarized_theme
            self._theme_engine.register(solarized_theme)
        except ImportError:
            pass

    def run(self) -> None:
        """Start the application. Blocks until quit."""
        try:
            asyncio.run(self._run_async())
        except KeyboardInterrupt:
            pass
        finally:
            self._shutdown()

    async def _run_async(self) -> None:
        self._backend = create_backend()
        self._backend.init()

        cols, rows = self._backend.get_size()
        self._screen = Screen(self._backend)

        self._window_manager = WindowManager(cols, rows)
        self._taskbar = TaskBar(self._window_manager)

        # Build UI tree
        self._build_root(cols, rows)

        # Set theme
        self._theme_engine.set_theme(self._initial_theme)

        self._event_loop = EventLoop(self._backend)
        self.running = True

        # Call user's on_ready
        self.on_ready()

        # Force initial full paint
        self._needs_repaint = True
        if self._screen:
            self._screen.force_full_redraw()

        # Run event loop
        await self._event_loop.run(self)

    def _build_root(self, cols: int, rows: int) -> None:
        self.root = Container(width=cols, height=rows)
        self.root._screen_rect = Rect(0, 0, cols, rows)
        self.root._theme_engine = self._theme_engine  # type: ignore

        # Desktop background
        self._desktop = Desktop()
        self._desktop.dock = "fill"
        self._desktop._screen_rect = Rect(0, 1, cols, rows - 2)
        # Give desktop theme access
        self._desktop.parent = self.root

        # Taskbar at bottom
        self._taskbar._screen_rect = Rect(0, rows - 1, cols, 1)
        self._taskbar.dock = "bottom"
        self._taskbar.parent = self.root

    def _shutdown(self) -> None:
        if self._backend:
            self._backend.shutdown()

    # --- Public API ---

    def on_ready(self) -> None:
        """Override this to set up your application UI."""
        pass

    def quit(self) -> None:
        """Stop the application."""
        self.running = False
        if self._event_loop:
            self._event_loop.stop()

    def add_window(self, window: Window) -> None:
        """Add a window to the application."""
        if self._window_manager:
            self._window_manager.add_window(window)
            # Give window theme access by parenting to root
            window.parent = self.root
            # Layout the window content
            window.arrange(window._screen_rect)
            self._needs_repaint = True

    def remove_window(self, window: Window) -> None:
        if self._window_manager:
            self._window_manager.remove_window(window)
            window.parent = None
            self._needs_repaint = True

    def set_menu(self, menu_bar: Widget) -> None:
        """Set the application menu bar."""
        self._menu_bar = menu_bar
        menu_bar.dock = "top"
        menu_bar.parent = self.root
        menu_bar._screen_rect = Rect(0, 0, self._screen.width if self._screen else 80, 1)
        self._needs_repaint = True

    def set_theme(self, name: str) -> None:
        """Switch to a different theme."""
        self._theme_engine.set_theme(name)
        self._needs_repaint = True
        if self._screen:
            self._screen.force_full_redraw()

    def call_later(self, delay: float, callback: Callable[[], None]) -> TimerHandle | None:
        if self._event_loop:
            return self._event_loop.call_later(delay, callback)
        return None

    def set_interval(self, interval: float, callback: Callable[[], None]) -> TimerHandle | None:
        if self._event_loop:
            return self._event_loop.set_interval(interval, callback)
        return None

    def invalidate_all(self) -> None:
        """Force full repaint."""
        self._needs_repaint = True
        if self._screen:
            self._screen.force_full_redraw()

    # --- Event Handling ---

    def _handle_resize(self, event: ResizeEvent) -> None:
        if self._screen:
            self._screen.resize(event.width, event.height)
        if self._window_manager:
            self._window_manager.resize_screen(event.width, event.height)
        if self.root:
            self.root.width = event.width
            self.root.height = event.height
            self.root._screen_rect = Rect(0, 0, event.width, event.height)

            if self._desktop:
                menu_h = 1 if self._menu_bar else 0
                self._desktop._screen_rect = Rect(0, menu_h, event.width, event.height - menu_h - 1)

            if self._taskbar:
                self._taskbar._screen_rect = Rect(0, event.height - 1, event.width, 1)

            if self._menu_bar:
                self._menu_bar._screen_rect = Rect(0, 0, event.width, 1)

        self.invalidate_all()

    def _handle_mouse(self, event: MouseEvent) -> None:
        # Update software cursor position
        self._mouse_cursor.move(event.x, event.y)
        # Always repaint because cursor moved
        self._needs_repaint = True

        # Process through tracker (detect drag, double-click)
        event = self._mouse_tracker.process(event)

        # --- Mouse capture: if something has capture, ALL events go to it ---
        if self._mouse_capture is not None:
            if event.action == MA.RELEASE:
                # Deliver release then free capture
                self._dispatch_to(event, self._mouse_capture)
                self._mouse_capture = None
                return
            elif event.action == MA.PRESS:
                # New press while captured — release old capture and
                # fall through to normal routing so the new target gets focus.
                self._mouse_capture = None
            else:
                self._dispatch_to(event, self._mouse_capture)
                return

        # Check modal dialogs first (children of root that are visible dialogs)
        for dialog in reversed(self._get_dialogs()):
            # Ensure dialog layout is up-to-date so child _screen_rects
            # are set before hit-testing (dialogs position children in paint)
            dialog.paint(Painter(
                self._screen.back,
                Rect(0, 0, self._screen.width, self._screen.height),
            ))
            hit = dialog.hit_test(event.x, event.y)
            if hit is not None:
                if event.action == MA.PRESS and event.button == MouseButton.LEFT:
                    self._mouse_capture = hit
                self._dispatch_to(event, hit)
                return
            # Click is outside the dialog but dialog is modal — consume event
            if event.action == MA.PRESS:
                return

        # Check taskbar first
        if self._taskbar and self._taskbar._screen_rect.contains(event.x, event.y):
            self._taskbar._invoke_handlers(event, Phase.BUBBLE)
            return

        # Check menu bar (both the bar itself and any open dropdown)
        if self._menu_bar:
            menu_hit = self._menu_bar.hit_test(event.x, event.y)
            if menu_hit is not None:
                self._dispatch_to(event, self._menu_bar)
                return

        # Close open menu if clicking elsewhere
        if (self._menu_bar and hasattr(self._menu_bar, '_menu_open')
                and self._menu_bar._menu_open
                and event.action == MA.PRESS):
            self._menu_bar._close_menu()

        # Route to window manager
        if self._window_manager:
            win = self._window_manager.hit_test(event.x, event.y)
            if win:
                if event.action == MA.PRESS and event.button == MouseButton.LEFT:
                    if win is not self._window_manager.active_window:
                        self._window_manager.activate(win)

                # Dispatch to the deepest widget under the mouse
                target = win.hit_test(event.x, event.y)
                if target:
                    # Capture the actual target so TUNNEL-phase handlers
                    # on ancestors (e.g. DesignSurface) stay in the
                    # dispatch path for drag/release events.
                    if event.action == MA.PRESS and event.button == MouseButton.LEFT:
                        self._mouse_capture = target
                    self._dispatch_to(event, target)
                else:
                    if event.action == MA.PRESS and event.button == MouseButton.LEFT:
                        self._mouse_capture = win
                    self._dispatch_to(event, win)
                return

    def _handle_event(self, event: Event) -> None:
        if isinstance(event, KeyEvent):
            self._handle_key(event)

    def _handle_key(self, event: KeyEvent) -> None:
        # Global shortcuts
        if event.key == Keys.CHAR and event.char == "q" and Modifiers.CTRL in event.modifiers:
            self.quit()
            event.mark_handled()
            return

        # If a modal dialog is open, route keys to it
        dialogs = self._get_dialogs()
        if dialogs:
            dialog = dialogs[-1]  # topmost

            # Tab / Shift+Tab: cycle focus within the dialog
            if event.key == Keys.TAB and event.modifiers in (Modifiers.NONE, Modifiers.SHIFT):
                focused = _find_focused(dialog)
                if focused:
                    if event.modifiers == Modifiers.SHIFT:
                        focused.focus_prev()
                    else:
                        focused.focus_next()
                else:
                    # Nothing focused yet — focus first focusable child
                    from .widgets.base import _collect_focusable
                    focusable = _collect_focusable(dialog)
                    if focusable:
                        focusable[0].focus()
                self._needs_repaint = True
                event.mark_handled()
                return

            # Dispatch to focused child inside the dialog if one exists
            focused = _find_focused(dialog)
            if focused and focused is not dialog:
                self._dispatch_to(event, focused)
            else:
                self._dispatch_to(event, dialog)
            self._needs_repaint = True
            return

        # Alt+Tab: cycle windows
        if event.key == Keys.TAB and Modifiers.ALT in event.modifiers:
            if self._window_manager:
                if Modifiers.SHIFT in event.modifiers:
                    self._window_manager.cycle_prev()
                else:
                    self._window_manager.cycle_next()
                self._needs_repaint = True
            event.mark_handled()
            return

        # Tab: focus next within active window
        if event.key == Keys.TAB and event.modifiers == Modifiers.NONE:
            focused = self._find_focused()
            if focused:
                focused.focus_next()
                self._needs_repaint = True
            event.mark_handled()
            return

        if event.key == Keys.TAB and event.modifiers == Modifiers.SHIFT:
            focused = self._find_focused()
            if focused:
                focused.focus_prev()
                self._needs_repaint = True
            event.mark_handled()
            return

        # F10: activate menu
        if event.key == Keys.F10 and self._menu_bar:
            self._dispatch_to(event, self._menu_bar)
            self._needs_repaint = True
            return

        # Dispatch to focused widget
        focused = self._find_focused()
        if focused:
            self._dispatch_to(event, focused)
            self._needs_repaint = True
        elif self._window_manager and self._window_manager.active_window:
            self._dispatch_to(event, self._window_manager.active_window)
            self._needs_repaint = True

    def _dispatch_to(self, event: Event, target: Widget) -> None:
        if self._event_loop:
            self._event_loop.dispatcher.dispatch(event, target, Strategy.TUNNEL_THEN_BUBBLE)

    def _get_dialogs(self) -> list[Widget]:
        """Return visible dialog children of root (not desktop/taskbar)."""
        if not self.root:
            return []
        from .dialogs.base import Dialog
        return [
            c for c in self.root.children
            if isinstance(c, Dialog) and c.visible and not c.closed
        ]

    @staticmethod
    def _paint_widget_tree(painter: Painter, widget: Widget) -> None:
        """Recursively paint all visible children unconditionally."""
        for child in widget.children:
            if child.visible:
                child.paint(painter)
                child._needs_paint = False
                App._paint_widget_tree(painter, child)

    def _cleanup_dialogs(self) -> None:
        """Remove closed dialogs from root."""
        if not self.root:
            return
        from .dialogs.base import Dialog
        closed = [
            c for c in self.root.children
            if isinstance(c, Dialog) and (c.closed or not c.visible)
        ]
        for c in closed:
            self.root.remove_child(c)

    def _find_focused(self) -> Widget | None:
        # Search dialogs first
        for dialog in reversed(self._get_dialogs()):
            found = _find_focused(dialog)
            if found:
                return found
        # Search within active window first
        if self._window_manager and self._window_manager.active_window:
            found = _find_focused(self._window_manager.active_window)
            if found:
                return found
        # Then check menu bar
        if self._menu_bar:
            found = _find_focused(self._menu_bar)
            if found:
                return found
        return None

    # --- Paint & Flush ---

    def _paint(self) -> None:
        if not self._screen or not self.root:
            return

        if not self._needs_repaint:
            return

        buf = self._screen.back

        # Clear with desktop color
        bg = self._theme_engine.get_color("desktop.bg", Color.BLUE)
        fg = self._theme_engine.get_color("desktop.fg", Color.CYAN)
        buf.clear(fg, bg)

        painter = Painter(buf, Rect(0, 0, self._screen.width, self._screen.height))

        # 1. Paint desktop background
        if self._desktop:
            self._desktop.paint(painter)

        # 2. Paint menu bar (just the bar, not the dropdown)
        if self._menu_bar:
            self._menu_bar.paint(painter)

        # 3. Paint windows in z-order (bottom to top) via window manager
        if self._window_manager:
            self._window_manager.paint(painter)

        # 4. Paint menu dropdown overlay (on top of windows)
        if self._menu_bar and hasattr(self._menu_bar, '_menu_open') and self._menu_bar._menu_open:
            menu_idx = self._menu_bar._active_menu_index
            if 0 <= menu_idx < len(self._menu_bar.menus):
                self._menu_bar._paint_dropdown(painter, menu_idx)

        # 5. Paint modal dialogs (on top of windows)
        for dialog in self._get_dialogs():
            dialog.paint(painter)
            # Paint dialog's child widgets (buttons, inputs, lists)
            self._paint_widget_tree(painter, dialog)

        # 6. Remove closed dialogs
        self._cleanup_dialogs()

        # 7. Paint taskbar
        if self._taskbar:
            self._taskbar.paint(painter)

        # 8. Paint mouse cursor highlight (on top of everything)
        self._mouse_cursor.paint(buf)

        self._needs_repaint = False

    def _flush(self) -> None:
        if self._screen:
            self._screen.flush()

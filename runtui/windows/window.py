"""Window widget -- draggable, resizable window with title bar and chrome."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from ..core.event import KeyEvent, MouseEvent, WindowAction, WindowEvent
from ..core.keys import Keys, Modifiers, MouseAction as MA, MouseButton
from ..core.types import Attrs, BorderStyle, Color, Rect, Size
from ..core.unicode import string_width, truncate_to_width
from ..rendering.painter import Painter
from ..widgets.base import Widget

if TYPE_CHECKING:
    pass


class WindowState:
    NORMAL = "normal"
    MINIMIZED = "minimized"
    MAXIMIZED = "maximized"


class Window(Widget):
    """A top-level window with title bar, borders, and control buttons."""

    TITLE_BAR_HEIGHT = 1
    MIN_WINDOW_WIDTH = 16
    MIN_WINDOW_HEIGHT = 5

    def __init__(
        self,
        title: str = "Window",
        id: str | None = None,
        x: int = 2,
        y: int = 1,
        width: int = 40,
        height: int = 15,
        resizable: bool = True,
        closable: bool = True,
        minimizable: bool = True,
        maximizable: bool = True,
        border: BorderStyle = BorderStyle.SINGLE,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        self.title = title
        self.resizable = resizable
        self.closable = closable
        self.minimizable = minimizable
        self.maximizable = maximizable
        self.border = border
        self._on_close = on_close
        self._state = WindowState.NORMAL
        self._active = False

        # Store pre-maximize geometry for restore
        self._restore_rect = Rect(x, y, width, height)

        # Drag state
        self._dragging = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0

        # Resize state
        self._resizing = False
        self._resize_edge = ""  # "n", "s", "e", "w", "ne", "nw", "se", "sw"

        # Content widget
        self._content: Widget | None = None

        self.can_focus = True
        self.min_width = self.MIN_WINDOW_WIDTH
        self.min_height = self.MIN_WINDOW_HEIGHT

        self.on(MouseEvent, self._handle_mouse)
        self.on(KeyEvent, self._handle_key)

    @property
    def state(self) -> str:
        return self._state

    @property
    def is_active(self) -> bool:
        return self._active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        if self._active != value:
            self._active = value
            self.invalidate()

    @property
    def content_rect(self) -> Rect:
        """Area available for content (inside chrome)."""
        return Rect(
            self._screen_rect.x + 1,
            self._screen_rect.y + 1,
            max(0, self._screen_rect.width - 2),
            max(0, self._screen_rect.height - 2),
        )

    def set_content(self, widget: Widget) -> None:
        """Set the window's content widget."""
        if self._content:
            self.remove_child(self._content)
        self._content = widget
        self.add_child(widget)
        self.invalidate_layout()

    def arrange(self, rect: Rect) -> None:
        self._screen_rect = rect
        self.x = rect.x
        self.y = rect.y
        self.width = rect.width
        self.height = rect.height
        # Arrange content in the interior
        cr = self.content_rect
        if self._content and self._content.visible:
            self._content.arrange(cr)
        self._needs_layout = False

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        prefix = "window.active." if self._active else "window."
        bg = self.theme_color(f"{prefix}bg", self.theme_color("window.bg", Color.CYAN))
        fg = self.theme_color(f"{prefix}fg", self.theme_color("window.fg", Color.BLACK))
        border_fg = self.theme_color(f"{prefix}border", fg)
        title_fg = self.theme_color(f"{prefix}title", fg)
        title_bg = self.theme_color(f"{prefix}title.bg", bg)

        # Fill background
        painter.fill_rect(lx, ly, sr.width, sr.height, bg=bg)

        # Draw border
        border_style = self.border
        if self._active:
            border_style = BorderStyle.DOUBLE
        painter.draw_border(lx, ly, sr.width, sr.height, style=border_style, fg=border_fg, bg=bg)

        # Draw title bar
        self._paint_title_bar(painter, lx, ly, sr.width, title_fg, title_bg, border_fg, bg)

        # Draw shadow (2 chars right, 1 char down)
        shadow_color = self.theme_color("window.shadow", Color.BRIGHT_BLACK)
        # Right shadow
        for row in range(1, sr.height + 1):
            painter.put_char(lx + sr.width, ly + row, " ", bg=shadow_color)
            painter.put_char(lx + sr.width + 1, ly + row, " ", bg=shadow_color)
        # Bottom shadow
        for col in range(2, sr.width + 2):
            painter.put_char(lx + col, ly + sr.height, " ", bg=shadow_color)

    def _paint_title_bar(
        self, painter: Painter, lx: int, ly: int, width: int,
        title_fg: Color, title_bg: Color, border_fg: Color, bg: Color
    ) -> None:
        # Fill title bar
        for col in range(1, width - 1):
            painter.put_char(lx + col, ly, " ", fg=title_fg, bg=title_bg)

        # Control buttons on the left
        btn_x = lx + 1
        btn_fg = self.theme_color("window.button", title_fg)

        if self.closable:
            close_glyph = self.theme_glyph("window.close", "[x]")
            painter.put_str(btn_x, ly, close_glyph, fg=btn_fg, bg=title_bg)
            btn_x += string_width(close_glyph)

        if self.minimizable:
            min_glyph = self.theme_glyph("window.minimize", "[_]")
            painter.put_str(btn_x, ly, min_glyph, fg=btn_fg, bg=title_bg)
            btn_x += string_width(min_glyph)

        if self.maximizable:
            if self._state == WindowState.MAXIMIZED:
                max_glyph = self.theme_glyph("window.restore", "[r]")
            else:
                max_glyph = self.theme_glyph("window.maximize", "[^]")
            painter.put_str(btn_x, ly, max_glyph, fg=btn_fg, bg=title_bg)
            btn_x += string_width(max_glyph)

        # Title text centered in remaining space
        title_start = btn_x + 1
        title_space = width - (title_start - lx) - 1
        if title_space > 0 and self.title:
            title_text = truncate_to_width(self.title, title_space)
            # Center within the available space
            tw = string_width(title_text)
            title_offset = max(0, (title_space - tw) // 2)
            attrs = Attrs.BOLD if self._active else Attrs.NONE
            painter.put_str(
                title_start + title_offset, ly, title_text,
                fg=title_fg, bg=title_bg, attrs=attrs,
            )

    def _handle_mouse(self, event: MouseEvent) -> None:
        sr = self._screen_rect
        rx = event.x - sr.x  # Relative x
        ry = event.y - sr.y  # Relative y

        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            # Check title bar buttons
            if ry == 0:
                btn_x = 1
                if self.closable:
                    close_w = string_width(self.theme_glyph("window.close", "[x]"))
                    if btn_x <= rx < btn_x + close_w:
                        self._do_close()
                        event.mark_handled()
                        return
                    btn_x += close_w

                if self.minimizable:
                    min_w = string_width(self.theme_glyph("window.minimize", "[_]"))
                    if btn_x <= rx < btn_x + min_w:
                        self._do_minimize()
                        event.mark_handled()
                        return
                    btn_x += min_w

                if self.maximizable:
                    max_w = 3
                    if btn_x <= rx < btn_x + max_w:
                        self._do_toggle_maximize()
                        event.mark_handled()
                        return

                # Start drag
                self._dragging = True
                self._drag_offset_x = rx
                self._drag_offset_y = ry
                event.mark_handled()
                return

            # Check resize edges
            if self.resizable and self._state == WindowState.NORMAL:
                edge = self._get_resize_edge(rx, ry, sr.width, sr.height)
                if edge:
                    self._resizing = True
                    self._resize_edge = edge
                    event.mark_handled()
                    return

        elif event.action == MA.DRAG:
            if self._dragging and self._state != WindowState.MAXIMIZED:
                new_x = event.x - self._drag_offset_x
                new_y = event.y - self._drag_offset_y
                self._move_to(new_x, new_y)
                event.mark_handled()
                return

            if self._resizing:
                self._do_resize(event.x, event.y)
                event.mark_handled()
                return

        elif event.action == MA.RELEASE:
            self._dragging = False
            self._resizing = False

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._active:
            return
        # Alt+F4 to close
        if event.key == Keys.F4 and Modifiers.ALT in event.modifiers:
            self._do_close()
            event.mark_handled()

    def _get_resize_edge(self, rx: int, ry: int, w: int, h: int) -> str:
        """Determine which resize edge/corner was clicked."""
        on_top = ry == 0
        on_bottom = ry == h - 1
        on_left = rx == 0
        on_right = rx == w - 1

        if on_bottom and on_right:
            return "se"
        if on_bottom and on_left:
            return "sw"
        if on_top and on_right:
            return "ne"
        if on_top and on_left:
            return "nw"
        if on_bottom:
            return "s"
        if on_right:
            return "e"
        if on_left:
            return "w"
        return ""

    def _move_to(self, x: int, y: int) -> None:
        self.x = max(0, x)
        self.y = max(1, y)  # Reserve row 0 for menu bar

        # Ensure the title bar stays within the visible area so the
        # window can always be reached.  _screen_bounds is set by the
        # WindowManager when the window is added.
        bounds = getattr(self, "_screen_bounds", None)
        if bounds is not None:
            max_y = bounds[1] - 1  # at least 1 row visible
            self.y = min(self.y, max_y)
            max_x = bounds[0] - self.MIN_WINDOW_WIDTH // 2
            self.x = min(self.x, max_x)

        self._screen_rect = Rect(self.x, self.y, self.width, self.height)
        self.invalidate_layout()

    def _do_resize(self, mouse_x: int, mouse_y: int) -> None:
        sr = self._screen_rect
        x, y, w, h = sr.x, sr.y, sr.width, sr.height

        if "e" in self._resize_edge:
            w = max(self.min_width, mouse_x - x + 1)
        if "w" in self._resize_edge:
            new_x = min(mouse_x, x + w - self.min_width)
            w = w + (x - new_x)
            x = new_x
        if "s" in self._resize_edge:
            h = max(self.min_height, mouse_y - y + 1)
        if "n" in self._resize_edge:
            new_y = min(mouse_y, y + h - self.min_height)
            h = h + (y - new_y)
            y = new_y

        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self._screen_rect = Rect(x, y, w, h)
        self.invalidate_layout()

    def _do_close(self) -> None:
        self.emit(WindowEvent(action=WindowAction.CLOSE, window=self))
        if self._on_close:
            self._on_close()

    def _do_minimize(self) -> None:
        self._state = WindowState.MINIMIZED
        self.visible = False
        self.emit(WindowEvent(action=WindowAction.MINIMIZE, window=self))

    def _do_toggle_maximize(self) -> None:
        if self._state == WindowState.MAXIMIZED:
            self._do_restore()
        else:
            self._do_maximize()

    def _do_maximize(self) -> None:
        self._restore_rect = Rect(self.x, self.y, self.width, self.height)
        self._state = WindowState.MAXIMIZED
        self.emit(WindowEvent(action=WindowAction.MAXIMIZE, window=self))

    def _do_restore(self) -> None:
        self._state = WindowState.NORMAL
        self.visible = True
        r = self._restore_rect
        self.x = r.x
        self.y = r.y
        self.width = r.width
        self.height = r.height
        self._screen_rect = r
        self.invalidate_layout()
        self.emit(WindowEvent(action=WindowAction.RESTORE, window=self))

    def restore(self) -> None:
        """Public method to restore a minimized/maximized window."""
        self._do_restore()

"""TextInput widget -- single-line text input."""

from __future__ import annotations

from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, Modifiers, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Size
from ..core.unicode import char_width, string_width, truncate_to_width
from ..rendering.painter import Painter
from .base import Widget


class TextInput(Widget):
    """Single-line text input field."""

    def __init__(
        self,
        text: str = "",
        placeholder: str = "",
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 20,
        height: int = 1,
        max_length: int = 0,
        on_change: Callable[[str], None] | None = None,
        on_submit: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        self._text = text
        self.placeholder = placeholder
        self.max_length = max_length
        self._on_change = on_change
        self._on_submit = on_submit
        self._cursor_pos = len(text)
        self._scroll_offset = 0
        self._selection_start = -1
        self._selection_end = -1
        self.can_focus = True
        self.min_height = 1

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if self.max_length > 0:
            value = value[:self.max_length]
        if self._text != value:
            self._text = value
            self._cursor_pos = min(self._cursor_pos, len(value))
            self.invalidate()
            if self._on_change:
                self._on_change(value)

    @property
    def cursor_pos(self) -> int:
        return self._cursor_pos

    def measure(self, available: Size) -> Size:
        return Size(self.width or 20, 1)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width

        if self._focused:
            fg = self.theme_color("input.focused.fg", Color.WHITE)
            bg = self.theme_color("input.focused.bg", Color.BLUE)
        else:
            fg = self.theme_color("input.fg", Color.BLACK)
            bg = self.theme_color("input.bg", Color.CYAN)

        # Fill background
        painter.fill_rect(lx, ly, w, 1, bg=bg)

        # Show placeholder if empty and not focused
        if not self._text and not self._focused:
            placeholder_fg = self.theme_color("input.placeholder", Color.BRIGHT_BLACK)
            painter.put_str(lx, ly, self.placeholder, fg=placeholder_fg, bg=bg, max_width=w)
            return

        # Calculate visible portion
        self._ensure_cursor_visible(w)
        visible_text = self._text[self._scroll_offset:]

        # Draw text
        col = 0
        for i, ch in enumerate(visible_text):
            if col >= w:
                break
            abs_pos = self._scroll_offset + i
            # Highlight selection
            if self._selection_start >= 0 and self._selection_start <= abs_pos < self._selection_end:
                sel_fg = self.theme_color("input.selection.fg", Color.BLACK)
                sel_bg = self.theme_color("input.selection.bg", Color.CYAN)
                painter.put_char(lx + col, ly, ch, sel_fg, sel_bg)
            else:
                painter.put_char(lx + col, ly, ch, fg, bg)
            col += char_width(ch)

        # Draw cursor
        if self._focused:
            cursor_col = self._cursor_display_pos(w)
            if 0 <= cursor_col < w:
                cursor_fg = self.theme_color("input.cursor", Color.BLACK)
                cursor_bg = self.theme_color("input.cursor.bg", fg)
                ch = self._text[self._cursor_pos] if self._cursor_pos < len(self._text) else " "
                painter.put_char(lx + cursor_col, ly, ch, cursor_fg, cursor_bg, Attrs.REVERSE)

    def _ensure_cursor_visible(self, width: int) -> None:
        """Scroll to keep cursor visible."""
        if self._cursor_pos < self._scroll_offset:
            self._scroll_offset = self._cursor_pos
        else:
            # Calculate display width from scroll_offset to cursor
            display_w = string_width(self._text[self._scroll_offset:self._cursor_pos])
            while display_w >= width and self._scroll_offset < self._cursor_pos:
                self._scroll_offset += 1
                display_w = string_width(self._text[self._scroll_offset:self._cursor_pos])

    def _cursor_display_pos(self, width: int) -> int:
        """Get the display column of the cursor."""
        return string_width(self._text[self._scroll_offset:self._cursor_pos])

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused or not self.enabled:
            return

        if event.key == Keys.LEFT:
            if self._cursor_pos > 0:
                self._cursor_pos -= 1
                self.invalidate()
            event.mark_handled()
        elif event.key == Keys.RIGHT:
            if self._cursor_pos < len(self._text):
                self._cursor_pos += 1
                self.invalidate()
            event.mark_handled()
        elif event.key == Keys.HOME:
            self._cursor_pos = 0
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.END:
            self._cursor_pos = len(self._text)
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.BACKSPACE:
            if self._cursor_pos > 0:
                self._text = self._text[:self._cursor_pos - 1] + self._text[self._cursor_pos:]
                self._cursor_pos -= 1
                self.invalidate()
                if self._on_change:
                    self._on_change(self._text)
            event.mark_handled()
        elif event.key == Keys.DELETE:
            if self._cursor_pos < len(self._text):
                self._text = self._text[:self._cursor_pos] + self._text[self._cursor_pos + 1:]
                self.invalidate()
                if self._on_change:
                    self._on_change(self._text)
            event.mark_handled()
        elif event.key == Keys.ENTER:
            if self._on_submit:
                self._on_submit(self._text)
            event.mark_handled()
        elif event.key == Keys.CHAR and event.char and Modifiers.CTRL not in event.modifiers:
            self._insert_char(event.char)
            event.mark_handled()
        # Ctrl+A: select all
        elif event.key == Keys.CHAR and event.char == "a" and Modifiers.CTRL in event.modifiers:
            self._selection_start = 0
            self._selection_end = len(self._text)
            self.invalidate()
            event.mark_handled()

    def _insert_char(self, char: str) -> None:
        if self.max_length > 0 and len(self._text) >= self.max_length:
            return
        self._text = self._text[:self._cursor_pos] + char + self._text[self._cursor_pos:]
        self._cursor_pos += 1
        self.invalidate()
        if self._on_change:
            self._on_change(self._text)

    def _handle_mouse(self, event: MouseEvent) -> None:
        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            self.focus()
            # Calculate cursor position from click
            rx = event.x - self._screen_rect.x
            pos = self._scroll_offset
            col = 0
            while pos < len(self._text) and col < rx:
                col += char_width(self._text[pos])
                pos += 1
            self._cursor_pos = pos
            self.invalidate()
            event.mark_handled()

"""PasswordInput widget -- masked text input."""

from __future__ import annotations

from typing import Callable

from ..core.types import Attrs, Color, Size
from ..core.unicode import string_width
from ..rendering.painter import Painter
from .input import TextInput


class PasswordInput(TextInput):
    """Password input that masks characters with a mask character."""

    def __init__(
        self,
        text: str = "",
        placeholder: str = "Password",
        mask_char: str = "●",
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 20,
        height: int = 1,
        max_length: int = 0,
        on_change: Callable[[str], None] | None = None,
        on_submit: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(
            text=text,
            placeholder=placeholder,
            id=id, x=x, y=y, width=width, height=height,
            max_length=max_length,
            on_change=on_change,
            on_submit=on_submit,
        )
        self.mask_char = mask_char

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

        painter.fill_rect(lx, ly, w, 1, bg=bg)

        if not self._text and not self._focused:
            placeholder_fg = self.theme_color("input.placeholder", Color.BRIGHT_BLACK)
            painter.put_str(lx, ly, self.placeholder, fg=placeholder_fg, bg=bg, max_width=w)
            return

        # Draw masked text
        masked = self.mask_char * len(self._text)
        self._ensure_cursor_visible(w)
        visible = masked[self._scroll_offset:]
        painter.put_str(lx, ly, visible, fg=fg, bg=bg, max_width=w)

        # Draw cursor
        if self._focused:
            cursor_col = self._cursor_display_pos(w)
            if 0 <= cursor_col < w:
                painter.put_char(lx + cursor_col, ly, self.mask_char, fg, bg, Attrs.REVERSE)

"""Checkbox widget."""

from __future__ import annotations

from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Size
from ..core.unicode import string_width
from ..rendering.painter import Painter
from .base import Widget


class Checkbox(Widget):
    """A checkbox with a label."""

    def __init__(
        self,
        label: str = "",
        checked: bool = False,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        on_change: Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=1)
        self.label = label
        self._checked = checked
        self._on_change = on_change
        self.can_focus = True

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    @property
    def checked(self) -> bool:
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        if self._checked != value:
            self._checked = value
            self.invalidate()
            if self._on_change:
                self._on_change(value)

    def toggle(self) -> None:
        self.checked = not self._checked

    def measure(self, available: Size) -> Size:
        # [X] Label
        w = self.width or (string_width(self.label) + 4)
        return Size(min(w, available.width), 1)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        if self._focused:
            fg = self.theme_color("checkbox.focused.fg", Color.WHITE)
            bg = self.theme_color("checkbox.focused.bg", Color.BLUE)
        else:
            fg = self.theme_color("checkbox.fg", Color.BLACK)
            bg = self.theme_color("checkbox.bg", Color.CYAN)

        painter.fill_rect(lx, ly, sr.width, 1, bg=bg)

        if self._checked:
            glyph = self.theme_glyph("checkbox.checked", "[X]")
        else:
            glyph = self.theme_glyph("checkbox.unchecked", "[ ]")

        attrs = Attrs.BOLD if self._focused else Attrs.NONE
        text = f"{glyph} {self.label}"
        painter.put_str(lx, ly, text, fg=fg, bg=bg, attrs=attrs, max_width=sr.width)

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused or not self.enabled:
            return
        if event.key in (Keys.ENTER, Keys.SPACE):
            self.toggle()
            event.mark_handled()

    def _handle_mouse(self, event: MouseEvent) -> None:
        if event.action == MA.PRESS and event.button == MouseButton.LEFT and self.enabled:
            self.focus()
            self.toggle()
            event.mark_handled()

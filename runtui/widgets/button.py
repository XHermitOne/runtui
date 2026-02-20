"""Button widget -- clickable button with label."""

from __future__ import annotations

from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, MouseAction, MouseButton
from ..core.types import Attrs, Color, Size
from ..core.unicode import string_width
from ..rendering.painter import Painter
from .base import Widget


class Button(Widget):
    """A clickable button."""

    def __init__(
        self,
        text: str = "Button",
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 1,
        on_click: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        self._text = text
        self._on_click = on_click
        self._pressed = False
        self.can_focus = True

        # Register event handlers
        self.on(MouseEvent, self._handle_mouse)
        self.on(KeyEvent, self._handle_key)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if self._text != value:
            self._text = value
            self.invalidate()

    def measure(self, available: Size) -> Size:
        # Button: [ text ]
        w = self.width or (string_width(self._text) + 4)
        h = self.height or 1
        return Size(min(w, available.width), min(h, available.height))

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        if self._pressed:
            fg = self.theme_color("button.pressed.fg", Color.BLACK)
            bg = self.theme_color("button.pressed.bg", Color.WHITE)
        elif self._focused:
            fg = self.theme_color("button.focused.fg", Color.BLACK)
            bg = self.theme_color("button.focused.bg", Color.CYAN)
        else:
            fg = self.theme_color("button.fg", Color.BLACK)
            bg = self.theme_color("button.bg", Color.WHITE)

        attrs = Attrs.BOLD if self._focused else Attrs.NONE

        # Fill background
        painter.fill_rect(lx, ly, sr.width, sr.height, bg=bg)

        # Center text: [ text ]
        label = f"[ {self._text} ]"
        tw = string_width(label)
        available = sr.width
        offset = max(0, (available - tw) // 2)
        painter.put_str(lx + offset, ly, label, fg=fg, bg=bg, attrs=attrs, max_width=available)

    def _handle_mouse(self, event: MouseEvent) -> None:
        if not self.enabled:
            return
        if event.action == MouseAction.PRESS and event.button == MouseButton.LEFT:
            self._pressed = True
            self.focus()
            self.invalidate()
            event.mark_handled()
        elif event.action == MouseAction.RELEASE and event.button == MouseButton.LEFT:
            if self._pressed:
                self._pressed = False
                self.invalidate()
                self._do_click()
            event.mark_handled()

    def _handle_key(self, event: KeyEvent) -> None:
        if not self.enabled or not self._focused:
            return
        if event.key in (Keys.ENTER, Keys.SPACE):
            self._do_click()
            event.mark_handled()

    def _do_click(self) -> None:
        if self._on_click:
            self._on_click()

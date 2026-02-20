"""RadioButton and RadioGroup widgets."""

from __future__ import annotations

from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Size
from ..core.unicode import string_width
from ..rendering.painter import Painter
from .base import Widget


class RadioGroup:
    """Groups RadioButtons so only one can be selected at a time."""

    def __init__(self, on_change: Callable[[str], None] | None = None) -> None:
        self._buttons: list[RadioButton] = []
        self._selected: RadioButton | None = None
        self._on_change = on_change

    def add(self, button: RadioButton) -> None:
        button._group = self
        self._buttons.append(button)
        if button._selected and self._selected is None:
            self._selected = button

    @property
    def selected(self) -> RadioButton | None:
        return self._selected

    @property
    def selected_value(self) -> str:
        return self._selected.value if self._selected else ""

    def select(self, button: RadioButton) -> None:
        if self._selected is button:
            return
        if self._selected:
            self._selected._selected = False
            self._selected.invalidate()
        self._selected = button
        button._selected = True
        button.invalidate()
        if self._on_change:
            self._on_change(button.value)


class RadioButton(Widget):
    """A radio button with a label, part of a RadioGroup."""

    def __init__(
        self,
        label: str = "",
        value: str = "",
        selected: bool = False,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        group: RadioGroup | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=1)
        self.label = label
        self.value = value or label
        self._selected = selected
        self._group: RadioGroup | None = group
        self.can_focus = True

        if group:
            group.add(self)

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    @property
    def selected(self) -> bool:
        return self._selected

    def select(self) -> None:
        if self._group:
            self._group.select(self)
        else:
            self._selected = True
            self.invalidate()

    def measure(self, available: Size) -> Size:
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

        if self._selected:
            glyph = self.theme_glyph("radio.selected", "(*)")
        else:
            glyph = self.theme_glyph("radio.unselected", "( )")

        attrs = Attrs.BOLD if self._focused else Attrs.NONE
        text = f"{glyph} {self.label}"
        painter.put_str(lx, ly, text, fg=fg, bg=bg, attrs=attrs, max_width=sr.width)

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused or not self.enabled:
            return
        if event.key in (Keys.ENTER, Keys.SPACE):
            self.select()
            event.mark_handled()

    def _handle_mouse(self, event: MouseEvent) -> None:
        if event.action == MA.PRESS and event.button == MouseButton.LEFT and self.enabled:
            self.focus()
            self.select()
            event.mark_handled()

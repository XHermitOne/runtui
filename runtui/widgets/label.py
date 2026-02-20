"""Label widget -- static text display."""

from __future__ import annotations

from ..core.types import Attrs, Color, Size
from ..core.unicode import string_width, truncate_to_width
from ..rendering.painter import Painter
from .base import Widget


class Label(Widget):
    """Displays static text."""

    def __init__(
        self,
        text: str = "",
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 1,
        align: str = "left",  # "left", "center", "right"
        fg: Color | None = None,
        bg: Color | None = None,
        bold: bool = False,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        self._text = text
        self.align = align
        self._fg = fg
        self._bg = bg
        self.bold = bold
        self.can_focus = False

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if self._text != value:
            self._text = value
            self.invalidate()

    def measure(self, available: Size) -> Size:
        w = self.width or string_width(self._text)
        h = self.height or 1
        return Size(min(w, available.width), min(h, available.height))

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        fg = self._fg or self.theme_color("label.fg", Color.WHITE)
        bg = self._bg or self.theme_color("label.bg", Color.DEFAULT)
        attrs = Attrs.BOLD if self.bold else Attrs.NONE

        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        # Clear area
        painter.fill_rect(lx, ly, sr.width, sr.height, bg=bg)

        # Calculate text position
        text = self._text
        tw = string_width(text)
        available = sr.width

        if tw > available:
            text = truncate_to_width(text, available)
            tw = available

        if self.align == "center":
            offset = (available - tw) // 2
        elif self.align == "right":
            offset = available - tw
        else:
            offset = 0

        painter.put_str(lx + offset, ly, text, fg=fg, bg=bg, attrs=attrs)

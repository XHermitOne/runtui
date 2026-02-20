"""ProgressBar widget -- bonus widget."""

from __future__ import annotations

from ..core.types import Attrs, Color, Size
from ..rendering.painter import Painter
from .base import Widget


class ProgressBar(Widget):
    """Horizontal progress bar."""

    def __init__(
        self,
        value: float = 0.0,
        max_value: float = 100.0,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 20,
        show_percentage: bool = True,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=1)
        self._value = value
        self._max_value = max_value
        self.show_percentage = show_percentage
        self.can_focus = False

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        v = max(0.0, min(v, self._max_value))
        if self._value != v:
            self._value = v
            self.invalidate()

    @property
    def percentage(self) -> float:
        if self._max_value <= 0:
            return 0.0
        return self._value / self._max_value * 100.0

    def measure(self, available: Size) -> Size:
        return Size(self.width or 20, 1)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width

        fg = self.theme_color("scrollbar.thumb", Color.GREEN)
        bg = self.theme_color("scrollbar.track", Color.BRIGHT_BLACK)
        text_fg = self.theme_color("label.fg", Color.WHITE)

        # Calculate filled portion
        ratio = self._value / self._max_value if self._max_value > 0 else 0
        filled = int(w * ratio)

        for col in range(w):
            if col < filled:
                painter.put_char(lx + col, ly, "█", fg, Color.DEFAULT)
            else:
                painter.put_char(lx + col, ly, "░", bg, Color.DEFAULT)

        # Overlay percentage text
        if self.show_percentage:
            pct = f"{self.percentage:.0f}%"
            px = lx + (w - len(pct)) // 2
            for i, ch in enumerate(pct):
                col = px + i - lx
                if col < filled:
                    painter.put_char(px + i, ly, ch, Color.BLACK, fg, Attrs.BOLD)
                else:
                    painter.put_char(px + i, ly, ch, text_fg, Color.DEFAULT, Attrs.BOLD)

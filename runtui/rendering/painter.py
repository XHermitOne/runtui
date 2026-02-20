"""Painter -- clipped drawing API for widgets."""

from __future__ import annotations

from ..core.types import Attrs, BorderChars, BorderStyle, Color, Point, Rect
from ..core.unicode import char_width, string_width, truncate_to_width
from .buffer import CellBuffer


class Painter:
    """Clipped drawing surface for a widget.

    All coordinates are relative to the clip region's origin.
    Drawing outside the clip region is silently clipped.
    """

    __slots__ = ("_buffer", "_clip", "_offset")

    def __init__(self, buffer: CellBuffer, clip: Rect, offset: Point | None = None) -> None:
        self._buffer = buffer
        self._clip = clip
        self._offset = offset or Point(clip.x, clip.y)

    @property
    def width(self) -> int:
        return self._clip.width

    @property
    def height(self) -> int:
        return self._clip.height

    def _to_screen(self, x: int, y: int) -> tuple[int, int]:
        """Convert local coords to screen coords."""
        return (x + self._offset.x, y + self._offset.y)

    def _in_clip(self, sx: int, sy: int) -> bool:
        """Check if screen coords are within clip region."""
        return self._clip.contains(sx, sy)

    def put_char(
        self,
        x: int,
        y: int,
        char: str,
        fg: Color = Color.DEFAULT,
        bg: Color = Color.DEFAULT,
        attrs: Attrs = Attrs.NONE,
    ) -> None:
        sx, sy = self._to_screen(x, y)
        if self._in_clip(sx, sy):
            self._buffer.put_char(sx, sy, char, fg, bg, attrs)

    def put_str(
        self,
        x: int,
        y: int,
        text: str,
        fg: Color = Color.DEFAULT,
        bg: Color = Color.DEFAULT,
        attrs: Attrs = Attrs.NONE,
        max_width: int | None = None,
    ) -> int:
        """Write text at position. Returns display width written."""
        if max_width is not None:
            text = truncate_to_width(text, max_width, ellipsis="")
        sx, sy = self._to_screen(x, y)
        if sy < self._clip.y or sy >= self._clip.bottom:
            return 0
        col = 0
        for ch in text:
            cw = char_width(ch)
            screen_x = sx + col
            if screen_x >= self._clip.right:
                break
            if screen_x >= self._clip.x:
                self._buffer.put_char(screen_x, sy, ch, fg, bg, attrs)
            col += cw
        return col

    def fill_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        char: str = " ",
        fg: Color = Color.DEFAULT,
        bg: Color = Color.DEFAULT,
        attrs: Attrs = Attrs.NONE,
    ) -> None:
        for row in range(height):
            for col in range(width):
                sx, sy = self._to_screen(x + col, y + row)
                if self._in_clip(sx, sy):
                    self._buffer.put_char(sx, sy, char, fg, bg, attrs)

    def draw_border(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        style: BorderStyle = BorderStyle.SINGLE,
        fg: Color = Color.DEFAULT,
        bg: Color = Color.DEFAULT,
        attrs: Attrs = Attrs.NONE,
    ) -> None:
        if width < 2 or height < 2:
            return
        chars = BorderChars.for_style(style)
        # Corners
        self.put_char(x, y, chars.top_left, fg, bg, attrs)
        self.put_char(x + width - 1, y, chars.top_right, fg, bg, attrs)
        self.put_char(x, y + height - 1, chars.bottom_left, fg, bg, attrs)
        self.put_char(x + width - 1, y + height - 1, chars.bottom_right, fg, bg, attrs)
        # Top and bottom edges
        for col in range(1, width - 1):
            self.put_char(x + col, y, chars.top, fg, bg, attrs)
            self.put_char(x + col, y + height - 1, chars.bottom, fg, bg, attrs)
        # Left and right edges
        for row in range(1, height - 1):
            self.put_char(x, y + row, chars.left, fg, bg, attrs)
            self.put_char(x + width - 1, y + row, chars.right, fg, bg, attrs)

    def draw_hline(
        self,
        x: int,
        y: int,
        width: int,
        char: str = "─",
        fg: Color = Color.DEFAULT,
        bg: Color = Color.DEFAULT,
        attrs: Attrs = Attrs.NONE,
    ) -> None:
        for col in range(width):
            self.put_char(x + col, y, char, fg, bg, attrs)

    def draw_vline(
        self,
        x: int,
        y: int,
        height: int,
        char: str = "│",
        fg: Color = Color.DEFAULT,
        bg: Color = Color.DEFAULT,
        attrs: Attrs = Attrs.NONE,
    ) -> None:
        for row in range(height):
            self.put_char(x, y + row, char, fg, bg, attrs)

    def sub_painter(self, x: int, y: int, width: int, height: int) -> Painter:
        """Create a sub-painter clipped to a sub-region."""
        sx, sy = self._to_screen(x, y)
        sub_rect = Rect(sx, sy, width, height)
        clipped = self._clip.intersect(sub_rect)
        return Painter(self._buffer, clipped, Point(sx, sy))

"""CellBuffer -- 2D grid of Cells for rendering."""

from __future__ import annotations

from ..core.types import Attrs, Cell, Color, Rect
from ..core.unicode import char_width


class CellBuffer:
    """A 2D grid of terminal cells."""

    __slots__ = ("width", "height", "_cells")

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._cells: list[list[Cell]] = [
            [Cell() for _ in range(width)] for _ in range(height)
        ]

    def get(self, x: int, y: int) -> Cell:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._cells[y][x]
        return Cell()

    def set(self, x: int, y: int, cell: Cell) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self._cells[y][x].copy_from(cell)

    def put_char(
        self,
        x: int,
        y: int,
        char: str,
        fg: Color = Color.DEFAULT,
        bg: Color = Color.DEFAULT,
        attrs: Attrs = Attrs.NONE,
    ) -> int:
        """Put a character at (x, y). Returns the display width consumed."""
        if not (0 <= y < self.height) or not (0 <= x < self.width):
            return 0
        cw = char_width(char) if char else 1
        cell = self._cells[y][x]
        cell.char = char
        cell.fg = fg
        cell.bg = bg
        cell.attrs = attrs
        cell.wide = False

        # For wide characters, mark the next cell as continuation
        if cw == 2 and x + 1 < self.width:
            next_cell = self._cells[y][x + 1]
            next_cell.char = ""
            next_cell.fg = fg
            next_cell.bg = bg
            next_cell.attrs = attrs
            next_cell.wide = True
        return cw

    def put_str(
        self,
        x: int,
        y: int,
        text: str,
        fg: Color = Color.DEFAULT,
        bg: Color = Color.DEFAULT,
        attrs: Attrs = Attrs.NONE,
    ) -> int:
        """Write a string starting at (x, y). Returns display width used."""
        if y < 0 or y >= self.height:
            return 0
        col = x
        for ch in text:
            if col >= self.width:
                break
            if col < 0:
                col += char_width(ch)
                continue
            cw = self.put_char(col, y, ch, fg, bg, attrs)
            col += cw
        return col - x

    def fill_rect(
        self,
        rect: Rect,
        char: str = " ",
        fg: Color = Color.DEFAULT,
        bg: Color = Color.DEFAULT,
        attrs: Attrs = Attrs.NONE,
    ) -> None:
        """Fill a rectangle with a character."""
        for row in range(rect.y, min(rect.bottom, self.height)):
            if row < 0:
                continue
            for col in range(rect.x, min(rect.right, self.width)):
                if col < 0:
                    continue
                cell = self._cells[row][col]
                cell.char = char
                cell.fg = fg
                cell.bg = bg
                cell.attrs = attrs
                cell.wide = False

    def clear(
        self,
        fg: Color = Color.DEFAULT,
        bg: Color = Color.DEFAULT,
    ) -> None:
        """Clear entire buffer."""
        for row in self._cells:
            for cell in row:
                cell.char = " "
                cell.fg = fg
                cell.bg = bg
                cell.attrs = Attrs.NONE
                cell.wide = False

    def resize(self, width: int, height: int) -> None:
        """Resize the buffer, preserving content where possible."""
        new_cells = [
            [Cell() for _ in range(width)] for _ in range(height)
        ]
        for y in range(min(height, self.height)):
            for x in range(min(width, self.width)):
                new_cells[y][x].copy_from(self._cells[y][x])
        self._cells = new_cells
        self.width = width
        self.height = height

    def copy_from(self, other: CellBuffer) -> None:
        """Copy contents from another buffer of the same size."""
        for y in range(min(self.height, other.height)):
            for x in range(min(self.width, other.width)):
                self._cells[y][x].copy_from(other._cells[y][x])

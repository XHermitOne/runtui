"""Software mouse cursor rendering."""

from __future__ import annotations

from ..core.types import Attrs, Color
from ..rendering.buffer import CellBuffer


class MouseCursor:
    """Software-rendered mouse cursor.

    Instead of painting a glyph that destroys content, we simply
    reverse the colors of the cell under the cursor position.
    This gives a visible pointer without hiding what's underneath.
    """

    def __init__(self) -> None:
        self.x = 0
        self.y = 0
        self.visible = True

    def move(self, x: int, y: int) -> None:
        self.x = max(0, x)
        self.y = max(0, y)

    def paint(self, buffer: CellBuffer) -> None:
        """Highlight the cell under the cursor by reversing its colors."""
        if not self.visible:
            return
        if self.x >= buffer.width or self.y >= buffer.height:
            return

        cell = buffer.get(self.x, self.y)
        # Swap fg/bg to create a visible highlight
        old_fg = cell.fg
        old_bg = cell.bg
        cell.fg = old_bg
        cell.bg = old_fg
        cell.attrs = cell.attrs | Attrs.BOLD

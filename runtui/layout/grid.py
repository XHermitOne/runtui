"""GridLayout -- rows x columns grid layout."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.types import Rect, Size
from .base import LayoutManager

if TYPE_CHECKING:
    from ..widgets.base import Widget


class GridLayout(LayoutManager):
    """Grid layout with specified rows and columns.

    Children are placed left-to-right, top-to-bottom.
    Each child can have `grid_row`, `grid_col`, `grid_row_span`, `grid_col_span` attributes.
    If not set, children are auto-placed sequentially.
    """

    def __init__(self, rows: int = 1, cols: int = 1, h_gap: int = 0, v_gap: int = 0) -> None:
        self.rows = max(1, rows)
        self.cols = max(1, cols)
        self.h_gap = h_gap
        self.v_gap = v_gap

    def measure(self, container: Widget, available: Size) -> Size:
        return available

    def arrange(self, container: Widget, rect: Rect) -> None:
        total_h_gap = self.h_gap * (self.cols - 1)
        total_v_gap = self.v_gap * (self.rows - 1)
        cell_w = (rect.width - total_h_gap) // self.cols if self.cols > 0 else rect.width
        cell_h = (rect.height - total_v_gap) // self.rows if self.rows > 0 else rect.height

        auto_row = 0
        auto_col = 0

        for child in container.children:
            if not child.visible:
                continue

            # Get grid position (manual or auto)
            row = getattr(child, "grid_row", -1)
            col = getattr(child, "grid_col", -1)
            row_span = getattr(child, "grid_row_span", 1)
            col_span = getattr(child, "grid_col_span", 1)

            if row < 0 or col < 0:
                row = auto_row
                col = auto_col
                auto_col += 1
                if auto_col >= self.cols:
                    auto_col = 0
                    auto_row += 1

            x = rect.x + col * (cell_w + self.h_gap)
            y = rect.y + row * (cell_h + self.v_gap)
            w = cell_w * col_span + self.h_gap * (col_span - 1)
            h = cell_h * row_span + self.v_gap * (row_span - 1)

            child.arrange(Rect(x, y, w, h))

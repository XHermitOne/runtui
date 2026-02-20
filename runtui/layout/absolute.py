"""Absolute layout -- children positioned manually."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.types import Rect, Size
from .base import LayoutManager

if TYPE_CHECKING:
    from ..widgets.base import Widget


class AbsoluteLayout(LayoutManager):
    """Layout where each child specifies its own x, y, width, height.

    Stores the original relative positions on first arrange so that
    repeated calls to arrange() don't compound the container offset.
    """

    def __init__(self) -> None:
        self._original_positions: dict[int, tuple[int, int, int, int]] = {}

    def measure(self, container: Widget, available: Size) -> Size:
        return available

    def arrange(self, container: Widget, rect: Rect) -> None:
        for child in container.children:
            if not child.visible:
                continue
            child_id = id(child)
            if child_id not in self._original_positions:
                # Store the original relative x, y, width, height
                self._original_positions[child_id] = (
                    child.x, child.y, child.width, child.height
                )
            ox, oy, ow, oh = self._original_positions[child_id]
            child.arrange(Rect(
                rect.x + ox,
                rect.y + oy,
                ow or rect.width,
                oh or rect.height,
            ))

"""Box layouts -- HBox and VBox linear stacking."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.types import Rect, Size
from .base import LayoutManager

if TYPE_CHECKING:
    from ..widgets.base import Widget


class HBoxLayout(LayoutManager):
    """Horizontal box layout -- children arranged left to right.

    Children with flex > 0 share remaining space proportionally.
    Children with flex == 0 use their measured width.
    """

    def __init__(self, spacing: int = 0) -> None:
        self.spacing = spacing

    def measure(self, container: Widget, available: Size) -> Size:
        total_w = 0
        max_h = 0
        for child in container.children:
            if not child.visible:
                continue
            sz = child.measure(available)
            total_w += sz.width + self.spacing
            max_h = max(max_h, sz.height)
        if total_w > 0:
            total_w -= self.spacing
        return Size(total_w, max_h)

    def arrange(self, container: Widget, rect: Rect) -> None:
        visible = [c for c in container.children if c.visible]
        if not visible:
            return

        # Measure fixed-size children
        total_fixed = 0
        total_flex = 0.0
        for child in visible:
            if child.flex > 0:
                total_flex += child.flex
            else:
                sz = child.measure(Size(rect.width, rect.height))
                total_fixed += sz.width

        total_spacing = self.spacing * (len(visible) - 1)
        remaining = max(0, rect.width - total_fixed - total_spacing)

        x = rect.x
        for child in visible:
            if child.flex > 0:
                w = int(remaining * child.flex / total_flex) if total_flex > 0 else 0
            else:
                w = child.measure(Size(rect.width, rect.height)).width
            child.arrange(Rect(x, rect.y, w, rect.height))
            x += w + self.spacing


class VBoxLayout(LayoutManager):
    """Vertical box layout -- children arranged top to bottom.

    Children with flex > 0 share remaining space proportionally.
    Children with flex == 0 use their measured height.
    """

    def __init__(self, spacing: int = 0) -> None:
        self.spacing = spacing

    def measure(self, container: Widget, available: Size) -> Size:
        max_w = 0
        total_h = 0
        for child in container.children:
            if not child.visible:
                continue
            sz = child.measure(available)
            max_w = max(max_w, sz.width)
            total_h += sz.height + self.spacing
        if total_h > 0:
            total_h -= self.spacing
        return Size(max_w, total_h)

    def arrange(self, container: Widget, rect: Rect) -> None:
        visible = [c for c in container.children if c.visible]
        if not visible:
            return

        total_fixed = 0
        total_flex = 0.0
        for child in visible:
            if child.flex > 0:
                total_flex += child.flex
            else:
                sz = child.measure(Size(rect.width, rect.height))
                total_fixed += sz.height

        total_spacing = self.spacing * (len(visible) - 1)
        remaining = max(0, rect.height - total_fixed - total_spacing)

        y = rect.y
        for child in visible:
            if child.flex > 0:
                h = int(remaining * child.flex / total_flex) if total_flex > 0 else 0
            else:
                h = child.measure(Size(rect.width, rect.height)).height
            child.arrange(Rect(rect.x, y, rect.width, h))
            y += h + self.spacing

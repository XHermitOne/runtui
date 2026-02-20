"""DockLayout -- dock children to edges or fill remaining space."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.types import Rect, Size
from .base import LayoutManager

if TYPE_CHECKING:
    from ..widgets.base import Widget


class DockLayout(LayoutManager):
    """Layout that docks children to top/bottom/left/right/fill.

    Each child's `dock` attribute determines placement:
        "top"    - full width, at top of remaining space
        "bottom" - full width, at bottom of remaining space
        "left"   - full height, at left of remaining space
        "right"  - full height, at right of remaining space
        "fill"   - fills all remaining space (should be last)

    Children are processed in order, each reducing the remaining space.
    """

    def measure(self, container: Widget, available: Size) -> Size:
        return available

    def arrange(self, container: Widget, rect: Rect) -> None:
        remaining = Rect(rect.x, rect.y, rect.width, rect.height)

        for child in container.children:
            if not child.visible:
                continue

            dock = getattr(child, "dock", "fill")

            if dock == "top":
                h = child.height or child.measure(Size(remaining.width, remaining.height)).height
                h = min(h, remaining.height)
                child.arrange(Rect(remaining.x, remaining.y, remaining.width, h))
                remaining = Rect(remaining.x, remaining.y + h, remaining.width, remaining.height - h)

            elif dock == "bottom":
                h = child.height or child.measure(Size(remaining.width, remaining.height)).height
                h = min(h, remaining.height)
                child.arrange(Rect(remaining.x, remaining.bottom - h, remaining.width, h))
                remaining = Rect(remaining.x, remaining.y, remaining.width, remaining.height - h)

            elif dock == "left":
                w = child.width or child.measure(Size(remaining.width, remaining.height)).width
                w = min(w, remaining.width)
                child.arrange(Rect(remaining.x, remaining.y, w, remaining.height))
                remaining = Rect(remaining.x + w, remaining.y, remaining.width - w, remaining.height)

            elif dock == "right":
                w = child.width or child.measure(Size(remaining.width, remaining.height)).width
                w = min(w, remaining.width)
                child.arrange(Rect(remaining.right - w, remaining.y, w, remaining.height))
                remaining = Rect(remaining.x, remaining.y, remaining.width - w, remaining.height)

            else:  # fill
                child.arrange(remaining)
                remaining = Rect(remaining.x, remaining.y, 0, 0)

"""Layout manager protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..core.types import Rect, Size

if TYPE_CHECKING:
    from ..widgets.base import Widget


class LayoutManager(ABC):
    """Abstract base for layout managers."""

    @abstractmethod
    def measure(self, container: Widget, available: Size) -> Size:
        """Calculate desired size for the container."""
        ...

    @abstractmethod
    def arrange(self, container: Widget, rect: Rect) -> None:
        """Position children within the given rect."""
        ...

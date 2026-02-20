"""Container widget -- holds and lays out child widgets."""

from __future__ import annotations

from ..core.types import Attrs, Color, Rect, Size, BorderStyle
from ..rendering.painter import Painter
from .base import Widget


class Container(Widget):
    """A widget that contains and manages child widgets.

    Can optionally draw a border and title.
    """

    def __init__(
        self,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 0,
        height: int = 0,
        border: BorderStyle = BorderStyle.NONE,
        title: str = "",
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        self.border = border
        self.title = title

    @property
    def has_border(self) -> bool:
        return self.border != BorderStyle.NONE

    @property
    def content_rect(self) -> Rect:
        """Return rect for child content, inset by border if present."""
        if self.has_border:
            return self._screen_rect.inset(top=1, right=1, bottom=1, left=1)
        return self._screen_rect

    def arrange(self, rect: Rect) -> None:
        self._screen_rect = rect
        self.x = rect.x
        self.y = rect.y
        self.width = rect.width
        self.height = rect.height

        content = self.content_rect
        if self._layout_manager and self.children:
            self._layout_manager.arrange(self, content)
        else:
            # Default: give each child the full content area
            for child in self.children:
                if child.visible:
                    child.arrange(content)
        self._needs_layout = False

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        bg = self.theme_color("container.bg", Color.DEFAULT)
        fg = self.theme_color("container.fg", Color.DEFAULT)
        border_fg = self.theme_color("container.border", fg)

        # Fill background
        painter.fill_rect(
            sr.x - painter._offset.x,
            sr.y - painter._offset.y,
            sr.width,
            sr.height,
            bg=bg,
        )

        # Draw border
        if self.has_border:
            painter.draw_border(
                sr.x - painter._offset.x,
                sr.y - painter._offset.y,
                sr.width,
                sr.height,
                style=self.border,
                fg=border_fg,
                bg=bg,
            )
            # Draw title
            if self.title and sr.width > 4:
                title_text = f" {self.title} "
                title_fg = self.theme_color("container.title", fg)
                painter.put_str(
                    sr.x - painter._offset.x + 2,
                    sr.y - painter._offset.y,
                    title_text,
                    fg=title_fg,
                    bg=bg,
                    max_width=sr.width - 4,
                )

    def paint_if_needed(self, painter: Painter) -> None:
        if not self.visible:
            return
        if self._needs_paint:
            self.paint(painter)
            self._needs_paint = False
        # Paint children
        for child in self.children:
            child.paint_if_needed(painter)

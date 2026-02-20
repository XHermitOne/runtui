"""Base modal dialog."""

from __future__ import annotations

from typing import Any

from ..core.event import KeyEvent
from ..core.keys import Keys
from ..core.types import BorderStyle, Color, Rect, Size, Attrs
from ..core.unicode import string_width
from ..rendering.painter import Painter
from ..widgets.base import Widget
from ..widgets.container import Container


class Dialog(Container):
    """Modal dialog base class.

    Dialogs are centered windows with OK/Cancel buttons.
    When shown modally, they capture all input until dismissed.
    """

    def __init__(
        self,
        title: str = "Dialog",
        width: int = 40,
        height: int = 12,
        id: str | None = None,
    ) -> None:
        super().__init__(
            id=id, width=width, height=height,
            border=BorderStyle.DOUBLE, title=title,
        )
        self._result: Any = None
        self._closed = False
        self.can_focus = True

        self.on(KeyEvent, self._handle_dialog_key)

    @property
    def result(self) -> Any:
        return self._result

    @property
    def closed(self) -> bool:
        return self._closed

    def center_on_screen(self, screen_width: int, screen_height: int) -> None:
        """Center the dialog on screen."""
        self.x = max(0, (screen_width - self.width) // 2)
        self.y = max(0, (screen_height - self.height) // 2)
        self._screen_rect = Rect(self.x, self.y, self.width, self.height)

    def close(self, result: Any = None) -> None:
        self._result = result
        self._closed = True
        self.visible = False

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("dialog.bg", Color.BRIGHT_BLACK)
        fg = self.theme_color("dialog.fg", Color.BLACK)
        border_fg = self.theme_color("dialog.border", Color.WHITE)
        title_fg = self.theme_color("dialog.title", Color.WHITE)

        # Fill background
        painter.fill_rect(lx, ly, sr.width, sr.height, bg=bg)

        # Draw border
        painter.draw_border(lx, ly, sr.width, sr.height,
                           style=self.border, fg=border_fg, bg=bg)

        # Draw title
        if self.title and sr.width > 4:
            title_text = f" {self.title} "
            tw = string_width(title_text)
            tx = lx + (sr.width - tw) // 2
            painter.put_str(tx, ly, title_text, fg=title_fg, bg=bg, attrs=Attrs.BOLD)

        # Shadow
        shadow_color = self.theme_color("window.shadow", Color.BRIGHT_BLACK)
        for row in range(1, sr.height + 1):
            painter.put_char(lx + sr.width, ly + row, " ", bg=shadow_color)
            painter.put_char(lx + sr.width + 1, ly + row, " ", bg=shadow_color)
        for col in range(2, sr.width + 2):
            painter.put_char(lx + col, ly + sr.height, " ", bg=shadow_color)

    def _handle_dialog_key(self, event: KeyEvent) -> None:
        if event.key == Keys.ESCAPE:
            self.close(None)
            event.mark_handled()

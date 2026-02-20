"""MessageBox dialog."""

from __future__ import annotations

from ..core.types import Color, Size
from ..core.unicode import string_width, split_by_width
from ..rendering.painter import Painter
from ..widgets.button import Button
from ..widgets.label import Label
from ..layout.box import VBoxLayout
from .base import Dialog


class MessageBox(Dialog):
    """A simple message box with title, message, and OK button."""

    def __init__(
        self,
        title: str = "Message",
        message: str = "",
        width: int = 40,
        buttons: list[str] | None = None,
    ) -> None:
        buttons = buttons or ["OK"]
        # Calculate height based on message
        lines = split_by_width(message, width - 4)
        height = max(8, len(lines) + 6)
        super().__init__(title=title, width=width, height=height)

        self._message = message
        self._button_labels = buttons
        self._buttons: list[Button] = []

        # Create button widgets
        for i, label in enumerate(buttons):
            btn = Button(text=label, on_click=lambda l=label: self.close(l))
            self._buttons.append(btn)
            self.add_child(btn)

    def paint(self, painter: Painter) -> None:
        super().paint(painter)

        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        content_w = sr.width - 4

        bg = self.theme_color("dialog.bg", Color.BRIGHT_BLACK)
        fg = self.theme_color("dialog.fg", Color.BLACK)

        # Draw message text
        lines = split_by_width(self._message, content_w)
        for i, line in enumerate(lines):
            painter.put_str(lx + 2, ly + 2 + i, line, fg=fg, bg=bg, max_width=content_w)

        # Position and draw buttons at bottom
        btn_y = ly + sr.height - 3
        total_btn_w = sum(string_width(b.text) + 4 for b in self._buttons)
        total_btn_w += len(self._buttons) - 1  # spacing
        btn_x = lx + (sr.width - total_btn_w) // 2

        for btn in self._buttons:
            btn_w = string_width(btn.text) + 4
            btn._screen_rect = __import__('runtui.core.types', fromlist=['Rect']).Rect(
                btn_x + painter._offset.x,
                btn_y + painter._offset.y,
                btn_w, 1,
            )
            btn.paint(painter)
            btn_x += btn_w + 1

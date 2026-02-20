"""Taskbar -- bottom bar showing minimized windows and clock."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Callable

from ..core.event import MouseEvent
from ..core.keys import MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Rect, Size
from ..core.unicode import string_width, truncate_to_width
from ..rendering.painter import Painter
from ..widgets.base import Widget

if TYPE_CHECKING:
    from .window import Window
    from .window_manager import WindowManager


class TaskBar(Widget):
    """Bottom taskbar showing window buttons and clock."""

    def __init__(self, window_manager: WindowManager | None = None) -> None:
        super().__init__(height=1)
        self._wm = window_manager
        self.can_focus = False
        self._button_rects: list[tuple[Rect, Window]] = []
        self.on(MouseEvent, self._handle_mouse)

    def set_window_manager(self, wm: WindowManager) -> None:
        self._wm = wm

    def measure(self, available: Size) -> Size:
        return Size(available.width, 1)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("taskbar.bg", Color.BRIGHT_BLACK)
        fg = self.theme_color("taskbar.fg", Color.WHITE)
        active_bg = self.theme_color("taskbar.active.bg", Color.BLUE)
        active_fg = self.theme_color("taskbar.active.fg", Color.WHITE)

        # Fill background
        painter.fill_rect(lx, ly, sr.width, 1, bg=bg)

        self._button_rects.clear()

        if not self._wm:
            return

        # Draw window buttons
        x = lx + 1
        for win in self._wm.windows:
            label = truncate_to_width(win.title, 15)
            btn_text = f" {label} "
            btn_w = string_width(btn_text)

            if x + btn_w > lx + sr.width - 8:
                break

            is_active = win is self._wm.active_window and win.visible
            is_minimized = not win.visible

            if is_active:
                painter.put_str(x, ly, btn_text, fg=active_fg, bg=active_bg, attrs=Attrs.BOLD)
            elif is_minimized:
                painter.put_str(x, ly, btn_text, fg=fg, bg=bg, attrs=Attrs.DIM)
            else:
                painter.put_str(x, ly, btn_text, fg=fg, bg=bg)

            screen_x = x + painter._offset.x
            self._button_rects.append((
                Rect(screen_x, sr.y, btn_w, 1),
                win,
            ))
            x += btn_w + 1

        # Draw clock on right
        clock_str = time.strftime(" %H:%M ")
        clock_x = lx + sr.width - string_width(clock_str)
        painter.put_str(clock_x, ly, clock_str, fg=fg, bg=bg)

    def _handle_mouse(self, event: MouseEvent) -> None:
        if event.action != MA.PRESS or event.button != MouseButton.LEFT:
            return
        if not self._wm:
            return

        for rect, win in self._button_rects:
            if rect.contains(event.x, event.y):
                if not win.visible:
                    win.restore()
                self._wm.activate(win)
                event.mark_handled()
                return

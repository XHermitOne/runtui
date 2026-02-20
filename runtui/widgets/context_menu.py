"""ContextMenu widget -- right-click popup menu."""

from __future__ import annotations

from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Rect, Size
from ..core.unicode import string_width
from ..rendering.painter import Painter
from .base import Widget
from .menu import MenuItem


class ContextMenu(Widget):
    """A popup context menu shown on right-click."""

    def __init__(
        self,
        items: list[MenuItem] | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self.items: list[MenuItem] = items or []
        self._selected_index = -1
        self.visible = False
        self.can_focus = True

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    def show(self, x: int, y: int) -> None:
        """Show the context menu at position (x, y)."""
        self.x = x
        self.y = y
        w = self._calc_width()
        h = len(self.items) + 2
        self.width = w
        self.height = h
        self._screen_rect = Rect(x, y, w, h)
        self.visible = True
        self._selected_index = 0
        self.focus()
        self.invalidate()

    def hide(self) -> None:
        self.visible = False
        self._selected_index = -1
        self.blur()
        self.invalidate()

    def _calc_width(self) -> int:
        max_w = max(
            (string_width(item.label) + (string_width(item.shortcut) + 2 if item.shortcut else 0)
             for item in self.items if not item.is_separator),
            default=10,
        )
        return max_w + 6

    def paint(self, painter: Painter) -> None:
        if not self.visible:
            return
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("menu.bg", Color.CYAN)
        fg = self.theme_color("menu.fg", Color.BLACK)
        sel_bg = self.theme_color("menu.selected.bg", Color.GREEN)
        sel_fg = self.theme_color("menu.selected.fg", Color.BLACK)
        disabled_fg = self.theme_color("menu.disabled", Color.BRIGHT_BLACK)
        sep_ch = self.theme_glyph("menu.separator", "─")

        # Border
        painter.draw_border(lx, ly, sr.width, sr.height, fg=fg, bg=bg)

        # Items
        for row, item in enumerate(self.items):
            iy = ly + 1 + row
            if item.is_separator:
                painter.put_char(lx, iy, "├", fg, bg)
                for col in range(1, sr.width - 1):
                    painter.put_char(lx + col, iy, sep_ch, fg, bg)
                painter.put_char(lx + sr.width - 1, iy, "┤", fg, bg)
                continue

            is_selected = row == self._selected_index
            item_bg = sel_bg if is_selected else bg
            item_fg = sel_fg if is_selected else (fg if item.enabled else disabled_fg)

            for col in range(1, sr.width - 1):
                painter.put_char(lx + col, iy, " ", item_fg, item_bg)

            painter.put_str(lx + 2, iy, item.label, fg=item_fg, bg=item_bg,
                           max_width=sr.width - 4)

            if item.shortcut:
                sw = string_width(item.shortcut)
                painter.put_str(lx + sr.width - 2 - sw, iy, item.shortcut,
                               fg=item_fg, bg=item_bg)

        # Shadow
        shadow_color = self.theme_color("window.shadow", Color.BRIGHT_BLACK)
        for row in range(1, sr.height + 1):
            painter.put_char(lx + sr.width, ly + row, " ", bg=shadow_color)
        for col in range(1, sr.width + 1):
            painter.put_char(lx + col, ly + sr.height, " ", bg=shadow_color)

    def _select_next(self) -> None:
        if not self.items:
            return
        idx = self._selected_index
        for _ in range(len(self.items)):
            idx = (idx + 1) % len(self.items)
            if not self.items[idx].is_separator and self.items[idx].enabled:
                self._selected_index = idx
                self.invalidate()
                return

    def _select_prev(self) -> None:
        if not self.items:
            return
        idx = self._selected_index
        for _ in range(len(self.items)):
            idx = (idx - 1) % len(self.items)
            if not self.items[idx].is_separator and self.items[idx].enabled:
                self._selected_index = idx
                self.invalidate()
                return

    def _handle_key(self, event: KeyEvent) -> None:
        if not self.visible or not self._focused:
            return
        if event.key == Keys.UP:
            self._select_prev()
            event.mark_handled()
        elif event.key == Keys.DOWN:
            self._select_next()
            event.mark_handled()
        elif event.key == Keys.ENTER:
            if 0 <= self._selected_index < len(self.items):
                item = self.items[self._selected_index]
                if item.enabled and item.action:
                    self.hide()
                    item.action()
            event.mark_handled()
        elif event.key == Keys.ESCAPE:
            self.hide()
            event.mark_handled()

    def _handle_mouse(self, event: MouseEvent) -> None:
        if not self.visible:
            return
        sr = self._screen_rect

        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            if sr.contains(event.x, event.y):
                ry = event.y - sr.y - 1  # minus border
                if 0 <= ry < len(self.items):
                    item = self.items[ry]
                    if not item.is_separator and item.enabled:
                        if item.action:
                            self.hide()
                            item.action()
                event.mark_handled()
            else:
                self.hide()
                event.mark_handled()
        elif event.action == MA.MOVE and sr.contains(event.x, event.y):
            ry = event.y - sr.y - 1
            if 0 <= ry < len(self.items) and not self.items[ry].is_separator:
                self._selected_index = ry
                self.invalidate()

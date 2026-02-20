"""DropDownList widget -- collapsed/expanded selection list."""

from __future__ import annotations

from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Size
from ..core.unicode import string_width, truncate_to_width
from ..rendering.painter import Painter
from .base import Widget


class DropDownList(Widget):
    """Drop-down list selector."""

    MAX_VISIBLE_ITEMS = 8

    def __init__(
        self,
        items: list[str] | None = None,
        selected_index: int = 0,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 20,
        on_change: Callable[[int, str], None] | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=1)
        self._items: list[str] = items or []
        self._selected_index = selected_index if self._items else -1
        self._expanded = False
        self._highlight_index = selected_index
        self._scroll_y = 0
        self._on_change = on_change
        self.can_focus = True

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    @property
    def items(self) -> list[str]:
        return self._items

    @items.setter
    def items(self, value: list[str]) -> None:
        self._items = value
        self._selected_index = 0 if value else -1
        self._highlight_index = self._selected_index
        self.invalidate()

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @property
    def selected_item(self) -> str | None:
        if 0 <= self._selected_index < len(self._items):
            return self._items[self._selected_index]
        return None

    def select(self, index: int) -> None:
        if 0 <= index < len(self._items):
            self._selected_index = index
            self._highlight_index = index
            self._expanded = False
            self.invalidate()
            if self._on_change:
                self._on_change(index, self._items[index])

    @property
    def expanded(self) -> bool:
        return self._expanded

    def toggle(self) -> None:
        self._expanded = not self._expanded
        if self._expanded:
            self._highlight_index = self._selected_index
        self.invalidate()

    def measure(self, available: Size) -> Size:
        return Size(self.width or 20, 1)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width

        fg = self.theme_color("dropdown.fg", Color.BLACK)
        bg = self.theme_color("dropdown.bg", Color.CYAN)
        arrow = self.theme_glyph("dropdown.arrow", "▼")

        if self._focused:
            fg = self.theme_color("input.focused.fg", fg)
            bg = self.theme_color("input.focused.bg", bg)

        # Draw collapsed header
        painter.fill_rect(lx, ly, w, 1, bg=bg)
        selected_text = self._items[self._selected_index] if 0 <= self._selected_index < len(self._items) else ""
        painter.put_str(lx + 1, ly, truncate_to_width(selected_text, w - 3), fg=fg, bg=bg)
        painter.put_char(lx + w - 2, ly, arrow, fg=fg, bg=bg)

        # Note: expanded dropdown list is painted as an overlay by
        # WindowManager._paint_overlays() so it appears on top of siblings.

    def _paint_dropdown(self, painter: Painter, lx: int, ly: int, w: int) -> None:
        visible = min(len(self._items), self.MAX_VISIBLE_ITEMS)
        fg = self.theme_color("dropdown.fg", Color.BLACK)
        bg = self.theme_color("dropdown.bg", Color.CYAN)
        sel_fg = self.theme_color("listbox.selected.fg", Color.WHITE)
        sel_bg = self.theme_color("listbox.selected.bg", Color.GREEN)

        for row in range(visible):
            idx = self._scroll_y + row
            if idx >= len(self._items):
                break
            is_highlight = idx == self._highlight_index
            if is_highlight:
                painter.fill_rect(lx, ly + row, w, 1, bg=sel_bg)
                painter.put_str(lx + 1, ly + row, truncate_to_width(self._items[idx], w - 2), fg=sel_fg, bg=sel_bg, attrs=Attrs.BOLD)
            else:
                painter.fill_rect(lx, ly + row, w, 1, bg=bg)
                painter.put_str(lx + 1, ly + row, truncate_to_width(self._items[idx], w - 2), fg=fg, bg=bg)

    def hit_test(self, x: int, y: int) -> Widget | None:
        """Override to include dropdown area when expanded."""
        if not self.visible:
            return None
        if self._screen_rect.contains(x, y):
            return self
        if self._expanded:
            visible = min(len(self._items), self.MAX_VISIBLE_ITEMS)
            dropdown_rect = self._screen_rect.offset(0, 1)
            dropdown_rect = dropdown_rect.__class__(
                dropdown_rect.x, dropdown_rect.y, dropdown_rect.width, visible
            )
            if dropdown_rect.contains(x, y):
                return self
        return None

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused or not self.enabled:
            return

        if self._expanded:
            if event.key == Keys.UP:
                self._highlight_index = max(0, self._highlight_index - 1)
                self._ensure_highlight_visible()
                self.invalidate()
                event.mark_handled()
            elif event.key == Keys.DOWN:
                self._highlight_index = min(len(self._items) - 1, self._highlight_index + 1)
                self._ensure_highlight_visible()
                self.invalidate()
                event.mark_handled()
            elif event.key == Keys.ENTER:
                self.select(self._highlight_index)
                event.mark_handled()
            elif event.key == Keys.ESCAPE:
                self._expanded = False
                self.invalidate()
                event.mark_handled()
        else:
            if event.key in (Keys.ENTER, Keys.SPACE):
                self.toggle()
                event.mark_handled()
            elif event.key == Keys.UP:
                if self._selected_index > 0:
                    self.select(self._selected_index - 1)
                event.mark_handled()
            elif event.key == Keys.DOWN:
                if self._selected_index < len(self._items) - 1:
                    self.select(self._selected_index + 1)
                event.mark_handled()

    def _ensure_highlight_visible(self) -> None:
        visible = min(len(self._items), self.MAX_VISIBLE_ITEMS)
        if self._highlight_index < self._scroll_y:
            self._scroll_y = self._highlight_index
        elif self._highlight_index >= self._scroll_y + visible:
            self._scroll_y = self._highlight_index - visible + 1

    def _handle_mouse(self, event: MouseEvent) -> None:
        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            self.focus()
            sr = self._screen_rect
            ry = event.y - sr.y

            if ry == 0:
                self.toggle()
            elif self._expanded and ry > 0:
                idx = self._scroll_y + (ry - 1)
                if 0 <= idx < len(self._items):
                    self.select(idx)
            event.mark_handled()

"""ListBox widget -- scrollable list of selectable items."""

from __future__ import annotations

from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, Modifiers, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Size
from ..core.unicode import truncate_to_width
from ..rendering.painter import Painter
from .base import Widget


class ListBox(Widget):
    """A scrollable list of items with selection.

    Supports optional multi-selection via Shift (range) and Ctrl (toggle).
    Enable with multi_select=True.
    """

    def __init__(
        self,
        items: list[str] | None = None,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 20,
        height: int = 8,
        on_select: Callable[[int, str], None] | None = None,
        on_activate: Callable[[int, str], None] | None = None,
        multi_select: bool = False,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        self._items: list[str] = items or []
        self._selected_index = 0 if self._items else -1
        self._scroll_y = 0
        self._on_select = on_select
        self._on_activate = on_activate
        self.multi_select = multi_select
        self._selected_indices: set[int] = set()
        self._anchor_index: int = -1  # for Shift+click range selection
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
        self._selected_indices.clear()
        self._anchor_index = -1
        self._scroll_y = 0
        self.invalidate()

    @property
    def selected_indices(self) -> set[int]:
        """Return the set of selected indices (multi-select mode)."""
        return set(self._selected_indices)

    def clear_selection(self) -> None:
        """Clear all selections in multi-select mode."""
        self._selected_indices.clear()
        self.invalidate()

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @selected_index.setter
    def selected_index(self, value: int) -> None:
        if not self._items:
            return
        value = max(0, min(value, len(self._items) - 1))
        if self._selected_index != value:
            self._selected_index = value
            self._ensure_visible()
            self.invalidate()
            if self._on_select:
                self._on_select(value, self._items[value])

    @property
    def selected_item(self) -> str | None:
        if 0 <= self._selected_index < len(self._items):
            return self._items[self._selected_index]
        return None

    def add_item(self, item: str) -> None:
        self._items.append(item)
        if self._selected_index < 0:
            self._selected_index = 0
        self.invalidate()

    def remove_item(self, index: int) -> None:
        if 0 <= index < len(self._items):
            self._items.pop(index)
            if self._selected_index >= len(self._items):
                self._selected_index = len(self._items) - 1
            self.invalidate()

    def clear(self) -> None:
        self._items.clear()
        self._selected_index = -1
        self._scroll_y = 0
        self.invalidate()

    def measure(self, available: Size) -> Size:
        return Size(self.width or 20, self.height or min(8, len(self._items) + 1))

    def _ensure_visible(self) -> None:
        h = self._screen_rect.height
        if self._selected_index < self._scroll_y:
            self._scroll_y = self._selected_index
        elif self._selected_index >= self._scroll_y + h:
            self._scroll_y = self._selected_index - h + 1

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width
        h = sr.height

        fg = self.theme_color("listbox.fg", Color.BLACK)
        bg = self.theme_color("listbox.bg", Color.CYAN)
        sel_fg = self.theme_color("listbox.selected.fg", Color.WHITE)
        sel_bg = self.theme_color("listbox.selected.bg", Color.GREEN)

        painter.fill_rect(lx, ly, w, h, bg=bg)

        for row in range(h):
            idx = self._scroll_y + row
            if idx >= len(self._items):
                break
            item = self._items[idx]
            is_cursor = idx == self._selected_index
            is_multi_selected = self.multi_select and idx in self._selected_indices

            if is_cursor or is_multi_selected:
                painter.fill_rect(lx, ly + row, w, 1, bg=sel_bg)
                text = truncate_to_width(item, w)
                attrs = Attrs.BOLD if (self._focused and is_cursor) else Attrs.NONE
                painter.put_str(lx, ly + row, text, fg=sel_fg, bg=sel_bg, attrs=attrs)
            else:
                text = truncate_to_width(item, w)
                painter.put_str(lx, ly + row, text, fg=fg, bg=bg)

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused or not self.enabled:
            return

        # Multi-select Shift+Arrow handling
        if self.multi_select and Modifiers.SHIFT in event.modifiers:
            if event.key in (Keys.UP, Keys.DOWN):
                if self._anchor_index < 0:
                    self._anchor_index = self._selected_index
                new_idx = self._selected_index + (-1 if event.key == Keys.UP else 1)
                new_idx = max(0, min(new_idx, len(self._items) - 1))
                lo = min(self._anchor_index, new_idx)
                hi = max(self._anchor_index, new_idx)
                self._selected_indices = set(range(lo, hi + 1))
                self._selected_index = new_idx
                self._ensure_visible()
                self.invalidate()
                if self._on_select and 0 <= new_idx < len(self._items):
                    self._on_select(new_idx, self._items[new_idx])
                event.mark_handled()
                return

        if event.key == Keys.UP:
            if self.multi_select:
                self._anchor_index = max(0, self._selected_index - 1)
                self._selected_indices = {self._anchor_index}
            self.selected_index -= 1
            event.mark_handled()
        elif event.key == Keys.DOWN:
            if self.multi_select:
                self._anchor_index = min(len(self._items) - 1, self._selected_index + 1)
                self._selected_indices = {self._anchor_index}
            self.selected_index += 1
            event.mark_handled()
        elif event.key == Keys.HOME:
            self.selected_index = 0
            if self.multi_select:
                self._anchor_index = 0
                self._selected_indices = {0}
            event.mark_handled()
        elif event.key == Keys.END:
            self.selected_index = len(self._items) - 1
            if self.multi_select:
                self._anchor_index = self._selected_index
                self._selected_indices = {self._selected_index}
            event.mark_handled()
        elif event.key == Keys.PAGE_UP:
            self.selected_index -= self._screen_rect.height
            event.mark_handled()
        elif event.key == Keys.PAGE_DOWN:
            self.selected_index += self._screen_rect.height
            event.mark_handled()
        elif event.key == Keys.ENTER:
            if self._on_activate and 0 <= self._selected_index < len(self._items):
                self._on_activate(self._selected_index, self._items[self._selected_index])
            event.mark_handled()

    def _handle_mouse(self, event: MouseEvent) -> None:
        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            self.focus()
            ry = event.y - self._screen_rect.y
            idx = self._scroll_y + ry
            if 0 <= idx < len(self._items):
                if self.multi_select:
                    mods = getattr(event, 'modifiers', Modifiers.NONE)
                    if Modifiers.CTRL in mods:
                        # Ctrl+Click: toggle individual item
                        if idx in self._selected_indices:
                            self._selected_indices.discard(idx)
                        else:
                            self._selected_indices.add(idx)
                        self._selected_index = idx
                        self._anchor_index = idx
                        self._ensure_visible()
                        self.invalidate()
                        if self._on_select:
                            self._on_select(idx, self._items[idx])
                    elif Modifiers.SHIFT in mods and self._anchor_index >= 0:
                        # Shift+Click: range select from anchor
                        lo = min(self._anchor_index, idx)
                        hi = max(self._anchor_index, idx)
                        self._selected_indices = set(range(lo, hi + 1))
                        self._selected_index = idx
                        self._ensure_visible()
                        self.invalidate()
                        if self._on_select:
                            self._on_select(idx, self._items[idx])
                    else:
                        # Plain click: single select
                        if idx == self._selected_index and self._on_activate:
                            self._on_activate(idx, self._items[idx])
                        self._selected_indices = {idx}
                        self._anchor_index = idx
                        self.selected_index = idx
                else:
                    if idx == self._selected_index and self._on_activate:
                        self._on_activate(idx, self._items[idx])
                    self.selected_index = idx
            event.mark_handled()
        elif event.button == MouseButton.SCROLL_UP:
            self._scroll_y = max(0, self._scroll_y - 3)
            self.invalidate()
            event.mark_handled()
        elif event.button == MouseButton.SCROLL_DOWN:
            max_scroll = max(0, len(self._items) - self._screen_rect.height)
            self._scroll_y = min(max_scroll, self._scroll_y + 3)
            self.invalidate()
            event.mark_handled()

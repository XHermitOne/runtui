"""MenuBar, Menu, and MenuItem widgets."""

from __future__ import annotations

from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, Modifiers, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Rect, Size
from ..core.unicode import string_width, truncate_to_width
from ..rendering.painter import Painter
from .base import Widget


class MenuItem:
    """A single menu item."""

    def __init__(
        self,
        label: str = "",
        shortcut: str = "",
        action: Callable[[], None] | None = None,
        enabled: bool = True,
        is_separator: bool = False,
        submenu: Menu | None = None,
    ) -> None:
        self.label = label
        self.shortcut = shortcut
        self.action = action
        self.enabled = enabled
        self.is_separator = is_separator
        self.submenu = submenu

    @staticmethod
    def separator() -> MenuItem:
        return MenuItem(is_separator=True)

    @property
    def display_width(self) -> int:
        if self.is_separator:
            return 0
        w = string_width(self.label) + 2  # padding
        if self.shortcut:
            w += string_width(self.shortcut) + 2
        return w


class Menu:
    """A dropdown menu containing MenuItems."""

    def __init__(self, title: str, items: list[MenuItem] | None = None) -> None:
        self.title = title
        self.items: list[MenuItem] = items or []
        self._selected_index = -1
        self._open = False

    @property
    def width(self) -> int:
        max_w = max((item.display_width for item in self.items if not item.is_separator), default=10)
        return max(max_w + 4, string_width(self.title) + 4)

    def select_next(self) -> None:
        if not self.items:
            return
        start = self._selected_index
        idx = (start + 1) % len(self.items)
        while idx != start:
            if not self.items[idx].is_separator and self.items[idx].enabled:
                self._selected_index = idx
                return
            idx = (idx + 1) % len(self.items)
            if start < 0:
                start = 0

    def select_prev(self) -> None:
        if not self.items:
            return
        start = self._selected_index
        if start < 0:
            start = 0
        idx = (start - 1) % len(self.items)
        while idx != start:
            if not self.items[idx].is_separator and self.items[idx].enabled:
                self._selected_index = idx
                return
            idx = (idx - 1) % len(self.items)


class MenuBar(Widget):
    """Horizontal menu bar at the top of the application."""

    def __init__(
        self,
        menus: list[Menu] | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id, height=1)
        self.menus: list[Menu] = menus or []
        self._active_menu_index = -1
        self._menu_open = False
        self.dock = "top"
        self.can_focus = True

        # Cache menu positions
        self._menu_positions: list[tuple[int, int]] = []  # (x, width)

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    def measure(self, available: Size) -> Size:
        return Size(available.width, 1)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width

        bg = self.theme_color("menu.bg", Color.CYAN)
        fg = self.theme_color("menu.fg", Color.BLACK)
        sel_bg = self.theme_color("menu.selected.bg", Color.GREEN)
        sel_fg = self.theme_color("menu.selected.fg", Color.BLACK)

        # Fill bar
        painter.fill_rect(lx, ly, w, 1, bg=bg)

        # Draw menu titles
        self._menu_positions.clear()
        x = lx + 1
        for i, menu in enumerate(self.menus):
            title = f" {menu.title} "
            tw = string_width(title)
            self._menu_positions.append((x + painter._offset.x, tw))

            is_active = i == self._active_menu_index
            if is_active:
                painter.put_str(x, ly, title, fg=sel_fg, bg=sel_bg, attrs=Attrs.BOLD)
            else:
                painter.put_str(x, ly, title, fg=fg, bg=bg)
            x += tw

        # Note: dropdown is painted as an overlay by App._paint()
        # after windows, so it appears on top of all windows.

    def _paint_dropdown(self, painter: Painter, menu_idx: int) -> None:
        menu = self.menus[menu_idx]
        pos_x, _ = self._menu_positions[menu_idx]
        lx = pos_x - painter._offset.x
        ly = self._screen_rect.y - painter._offset.y + 1

        bg = self.theme_color("menu.bg", Color.CYAN)
        fg = self.theme_color("menu.fg", Color.BLACK)
        sel_bg = self.theme_color("menu.selected.bg", Color.GREEN)
        sel_fg = self.theme_color("menu.selected.fg", Color.BLACK)
        disabled_fg = self.theme_color("menu.disabled", Color.BRIGHT_BLACK)
        hotkey_fg = self.theme_color("menu.hotkey", Color.RED)
        sep_ch = self.theme_glyph("menu.separator", "─")

        menu_w = menu.width
        menu_h = len(menu.items) + 2  # top/bottom border

        # Draw border
        painter.draw_border(lx, ly, menu_w, menu_h, fg=fg, bg=bg)

        # Draw items
        for row, item in enumerate(menu.items):
            iy = ly + 1 + row
            if item.is_separator:
                painter.put_char(lx, iy, "├", fg, bg)
                for col in range(1, menu_w - 1):
                    painter.put_char(lx + col, iy, sep_ch, fg, bg)
                painter.put_char(lx + menu_w - 1, iy, "┤", fg, bg)
                continue

            is_selected = row == menu._selected_index
            item_bg = sel_bg if is_selected else bg
            item_fg = sel_fg if is_selected else (fg if item.enabled else disabled_fg)

            # Fill row
            for col in range(1, menu_w - 1):
                painter.put_char(lx + col, iy, " ", item_fg, item_bg)

            # Label
            painter.put_str(lx + 2, iy, item.label, fg=item_fg, bg=item_bg,
                           max_width=menu_w - 4)

            # Shortcut
            if item.shortcut:
                sw = string_width(item.shortcut)
                painter.put_str(lx + menu_w - 2 - sw, iy, item.shortcut,
                               fg=hotkey_fg if item.enabled else disabled_fg, bg=item_bg)

    def hit_test(self, x: int, y: int) -> Widget | None:
        if not self.visible:
            return None
        if self._screen_rect.contains(x, y):
            return self
        # Check if click is within open dropdown
        if self._menu_open and 0 <= self._active_menu_index < len(self.menus):
            menu = self.menus[self._active_menu_index]
            pos_x, _ = self._menu_positions[self._active_menu_index]
            menu_rect = Rect(pos_x, self._screen_rect.y + 1, menu.width, len(menu.items) + 2)
            if menu_rect.contains(x, y):
                return self
        return None

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused:
            # Check F10 to activate menu
            if event.key == Keys.F10:
                self.focus()
                self._active_menu_index = 0
                self._menu_open = True
                self.menus[0]._selected_index = 0
                self.invalidate()
                event.mark_handled()
            return

        if self._menu_open:
            menu = self.menus[self._active_menu_index]
            if event.key == Keys.UP:
                menu.select_prev()
                self.invalidate()
                event.mark_handled()
            elif event.key == Keys.DOWN:
                menu.select_next()
                self.invalidate()
                event.mark_handled()
            elif event.key == Keys.LEFT:
                self._active_menu_index = (self._active_menu_index - 1) % len(self.menus)
                self.menus[self._active_menu_index]._selected_index = 0
                self.invalidate()
                event.mark_handled()
            elif event.key == Keys.RIGHT:
                self._active_menu_index = (self._active_menu_index + 1) % len(self.menus)
                self.menus[self._active_menu_index]._selected_index = 0
                self.invalidate()
                event.mark_handled()
            elif event.key == Keys.ENTER:
                idx = menu._selected_index
                if 0 <= idx < len(menu.items):
                    item = menu.items[idx]
                    if item.enabled and item.action:
                        self._close_menu()
                        item.action()
                event.mark_handled()
            elif event.key == Keys.ESCAPE:
                self._close_menu()
                event.mark_handled()
        else:
            if event.key == Keys.ESCAPE:
                self.blur()
                event.mark_handled()

    def _close_menu(self) -> None:
        self._menu_open = False
        for menu in self.menus:
            menu._selected_index = -1
        self._active_menu_index = -1
        self.invalidate()

    def _handle_mouse(self, event: MouseEvent) -> None:
        if event.action != MA.PRESS or event.button != MouseButton.LEFT:
            return

        sr = self._screen_rect
        ry = event.y - sr.y

        # Click on menu bar
        if ry == 0:
            for i, (pos_x, tw) in enumerate(self._menu_positions):
                if pos_x <= event.x < pos_x + tw:
                    self.focus()
                    if self._active_menu_index == i and self._menu_open:
                        self._close_menu()
                    else:
                        self._active_menu_index = i
                        self._menu_open = True
                        self.menus[i]._selected_index = 0
                        self.invalidate()
                    event.mark_handled()
                    return
            return

        # Click in dropdown
        if self._menu_open and 0 <= self._active_menu_index < len(self.menus):
            menu = self.menus[self._active_menu_index]
            pos_x, _ = self._menu_positions[self._active_menu_index]
            item_row = ry - 1 - 1  # subtract bar row and border top
            if 0 <= item_row < len(menu.items):
                item = menu.items[item_row]
                if not item.is_separator and item.enabled and item.action:
                    self._close_menu()
                    item.action()
                    event.mark_handled()

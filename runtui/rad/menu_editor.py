"""Menu editor dialog and data model for the RAD designer."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from ..core.types import Color, Rect, Attrs
from ..core.unicode import string_width
from ..rendering.painter import Painter
from ..widgets.button import Button
from ..widgets.checkbox import Checkbox
from ..widgets.input import TextInput
from ..widgets.label import Label
from ..widgets.listbox import ListBox
from ..dialogs.base import Dialog


# ---------------------------------------------------------------------------
# Data model (plain dataclasses, no widget dependencies)
# ---------------------------------------------------------------------------

@dataclass
class MenuItemData:
    """A single menu item in the design data."""
    label: str = ""
    shortcut: str = ""
    enabled: bool = True
    is_separator: bool = False
    handler: str = ""


@dataclass
class MenuData:
    """A top-level menu in the design data."""
    title: str = ""
    items: list[MenuItemData] = field(default_factory=list)


@dataclass
class MenuDesignData:
    """All menus for a design."""
    menus: list[MenuData] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def menu_design_to_dict(data: MenuDesignData) -> list[dict]:
    """Serialize MenuDesignData to a JSON-compatible list of dicts."""
    result = []
    for menu in data.menus:
        items = []
        for item in menu.items:
            d: dict[str, Any] = {}
            if item.is_separator:
                d["is_separator"] = True
            else:
                if item.label:
                    d["label"] = item.label
                if item.shortcut:
                    d["shortcut"] = item.shortcut
                if item.handler:
                    d["handler"] = item.handler
                if not item.enabled:
                    d["enabled"] = False
            items.append(d)
        result.append({"title": menu.title, "items": items})
    return result


def dict_to_menu_design(raw: list[dict]) -> MenuDesignData:
    """Reconstruct MenuDesignData from a JSON-compatible list of dicts."""
    menus = []
    for menu_dict in raw:
        items = []
        for item_dict in menu_dict.get("items", []):
            items.append(MenuItemData(
                label=item_dict.get("label", ""),
                shortcut=item_dict.get("shortcut", ""),
                enabled=item_dict.get("enabled", True),
                is_separator=item_dict.get("is_separator", False),
                handler=item_dict.get("handler", ""),
            ))
        menus.append(MenuData(title=menu_dict.get("title", ""), items=items))
    return MenuDesignData(menus=menus)


def menu_design_to_live(data: MenuDesignData):
    """Create a live MenuBar widget from MenuDesignData.

    Returns a MenuBar or None if there are no menus.
    """
    if not data.menus:
        return None

    from ..widgets.menu import MenuBar, Menu, MenuItem

    live_menus = []
    for menu_data in data.menus:
        live_items = []
        for item_data in menu_data.items:
            if item_data.is_separator:
                live_items.append(MenuItem.separator())
            else:
                live_items.append(MenuItem(
                    label=item_data.label,
                    shortcut=item_data.shortcut,
                    enabled=item_data.enabled,
                ))
        live_menus.append(Menu(menu_data.title, live_items))

    return MenuBar(menus=live_menus)


# ---------------------------------------------------------------------------
# Menu Editor Dialog
# ---------------------------------------------------------------------------

_SEPARATOR_DISPLAY = "  ────────"


class MenuEditorDialog(Dialog):
    """Tree-based menu editor dialog.

    Left side: flattened tree view of menus and items.
    Right side: property fields for the selected entry.
    """

    def __init__(
        self,
        data: MenuDesignData | None = None,
        title: str = "Edit Menus",
        width: int = 62,
        height: int = 22,
    ) -> None:
        super().__init__(title=title, width=width, height=height)
        # Deep copy so Cancel discards changes
        self._data = copy.deepcopy(data) if data else MenuDesignData()

        # Parallel list mapping each tree row -> (menu_idx, item_idx | None)
        self._tree_entries: list[tuple[int, int | None]] = []

        # --- Left side widgets ---
        self._tree_list = ListBox(
            items=[],
            width=28, height=12,
            on_select=self._on_tree_select,
        )
        self.add_child(self._tree_list)

        self._btn_add_menu = Button(text="+Menu", width=7, on_click=self._add_menu)
        self._btn_add_item = Button(text="+Item", width=7, on_click=self._add_item)
        self._btn_add_sep = Button(text="+Sep", width=6, on_click=self._add_separator)
        self._btn_delete = Button(text="Delete", width=8, on_click=self._delete_entry)
        self._btn_up = Button(text="\u25b2 Up", width=6, on_click=self._move_up)
        self._btn_down = Button(text="\u25bc Dn", width=6, on_click=self._move_down)
        for btn in (self._btn_add_menu, self._btn_add_item, self._btn_add_sep,
                    self._btn_delete, self._btn_up, self._btn_down):
            self.add_child(btn)

        # --- Right side widgets (property editors) ---
        self._lbl_label = Label(text="Label:", width=9, bold=True)
        self._inp_label = TextInput(text="", width=18, on_change=self._on_label_changed)
        self._lbl_shortcut = Label(text="Shortcut:", width=9, bold=True)
        self._inp_shortcut = TextInput(text="", width=18, on_change=self._on_shortcut_changed)
        self._lbl_handler = Label(text="Handler:", width=9, bold=True)
        self._inp_handler = TextInput(text="", width=18, on_change=self._on_handler_changed)
        self._lbl_enabled = Label(text="Enabled:", width=9, bold=True)
        self._chk_enabled = Checkbox(label="", checked=True, on_change=self._on_enabled_changed)

        for w in (self._lbl_label, self._inp_label,
                  self._lbl_shortcut, self._inp_shortcut,
                  self._lbl_handler, self._inp_handler,
                  self._lbl_enabled, self._chk_enabled):
            self.add_child(w)

        # --- OK / Cancel ---
        self._btn_ok = Button(text="OK", width=10, on_click=self._on_ok)
        self._btn_cancel = Button(text="Cancel", width=10, on_click=self._on_cancel)
        self.add_child(self._btn_ok)
        self.add_child(self._btn_cancel)

        # Tracks whether property panel is showing menu-header, item, or nothing
        self._prop_mode: str = "none"  # "menu", "item", "separator", "none"

        self._rebuild_tree()

    # ------------------------------------------------------------------
    # Tree building
    # ------------------------------------------------------------------

    def _rebuild_tree(self) -> None:
        """Rebuild the flattened tree list from self._data."""
        items: list[str] = []
        entries: list[tuple[int, int | None]] = []

        for mi, menu in enumerate(self._data.menus):
            items.append(f"\u25bc {menu.title}")
            entries.append((mi, None))
            for ii, item in enumerate(menu.items):
                if item.is_separator:
                    items.append(_SEPARATOR_DISPLAY)
                else:
                    shortcut_suffix = f"  {item.shortcut}" if item.shortcut else ""
                    items.append(f"  {item.label}{shortcut_suffix}")
                entries.append((mi, ii))

        self._tree_entries = entries
        self._tree_list._items = items
        # Clamp selection
        if self._tree_list._selected_index >= len(items):
            self._tree_list._selected_index = max(0, len(items) - 1)
        self._tree_list.invalidate()
        self._update_properties()

    def _selected_entry(self) -> tuple[int, int | None] | None:
        idx = self._tree_list._selected_index
        if 0 <= idx < len(self._tree_entries):
            return self._tree_entries[idx]
        return None

    # ------------------------------------------------------------------
    # Property panel updates
    # ------------------------------------------------------------------

    def _update_properties(self) -> None:
        """Sync property fields to the currently selected tree entry."""
        entry = self._selected_entry()
        if entry is None:
            self._prop_mode = "none"
            return

        mi, ii = entry
        if ii is None:
            # Menu header selected
            self._prop_mode = "menu"
            menu = self._data.menus[mi]
            self._inp_label._text = menu.title
            self._inp_label._cursor_pos = len(menu.title)
            self._inp_shortcut._text = ""
            self._inp_handler._text = ""
            self._chk_enabled._checked = True
        else:
            item = self._data.menus[mi].items[ii]
            if item.is_separator:
                self._prop_mode = "separator"
            else:
                self._prop_mode = "item"
                self._inp_label._text = item.label
                self._inp_label._cursor_pos = len(item.label)
                self._inp_shortcut._text = item.shortcut
                self._inp_shortcut._cursor_pos = len(item.shortcut)
                self._inp_handler._text = item.handler
                self._inp_handler._cursor_pos = len(item.handler)
                self._chk_enabled._checked = item.enabled

        self.invalidate()

    # ------------------------------------------------------------------
    # Property change callbacks
    # ------------------------------------------------------------------

    def _on_label_changed(self, value: str) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        mi, ii = entry
        if ii is None:
            self._data.menus[mi].title = value
        else:
            self._data.menus[mi].items[ii].label = value
        self._rebuild_tree_preserve_selection()

    def _on_shortcut_changed(self, value: str) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        mi, ii = entry
        if ii is not None:
            self._data.menus[mi].items[ii].shortcut = value
            self._rebuild_tree_preserve_selection()

    def _on_handler_changed(self, value: str) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        mi, ii = entry
        if ii is not None:
            self._data.menus[mi].items[ii].handler = value

    def _on_enabled_changed(self, value: bool) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        mi, ii = entry
        if ii is not None:
            self._data.menus[mi].items[ii].enabled = value

    def _rebuild_tree_preserve_selection(self) -> None:
        """Rebuild tree but keep current selection index."""
        sel = self._tree_list._selected_index
        self._rebuild_tree()
        if sel < len(self._tree_entries):
            self._tree_list._selected_index = sel

    # ------------------------------------------------------------------
    # Tree selection callback
    # ------------------------------------------------------------------

    def _on_tree_select(self, idx: int, item: str) -> None:
        self._update_properties()
        self.invalidate()

    # ------------------------------------------------------------------
    # Button actions
    # ------------------------------------------------------------------

    def _add_menu(self) -> None:
        self._data.menus.append(MenuData(title="New Menu"))
        self._rebuild_tree()
        # Select the new menu header (last menu entry with item_idx=None)
        for i in range(len(self._tree_entries) - 1, -1, -1):
            if self._tree_entries[i][1] is None:
                self._tree_list._selected_index = i
                break
        self._update_properties()

    def _add_item(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            if not self._data.menus:
                return
            mi = len(self._data.menus) - 1
            insert_idx = len(self._data.menus[mi].items)
        else:
            mi, ii = entry
            if ii is None:
                insert_idx = len(self._data.menus[mi].items)
            else:
                insert_idx = ii + 1
        self._data.menus[mi].items.insert(insert_idx, MenuItemData(label="New Item"))
        self._rebuild_tree()
        # Select the newly added item
        target = (mi, insert_idx)
        for i, e in enumerate(self._tree_entries):
            if e == target:
                self._tree_list._selected_index = i
                break
        self._update_properties()

    def _add_separator(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            if not self._data.menus:
                return
            mi = len(self._data.menus) - 1
            insert_idx = len(self._data.menus[mi].items)
        else:
            mi, ii = entry
            if ii is None:
                insert_idx = len(self._data.menus[mi].items)
            else:
                insert_idx = ii + 1
        self._data.menus[mi].items.insert(insert_idx, MenuItemData(is_separator=True))
        self._rebuild_tree()
        target = (mi, insert_idx)
        for i, e in enumerate(self._tree_entries):
            if e == target:
                self._tree_list._selected_index = i
                break
        self._update_properties()

    def _delete_entry(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        mi, ii = entry
        if ii is None:
            # Delete entire menu
            del self._data.menus[mi]
        else:
            del self._data.menus[mi].items[ii]
        self._rebuild_tree()
        self._update_properties()

    def _move_up(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        mi, ii = entry
        if ii is None:
            # Move menu up
            if mi <= 0:
                return
            self._data.menus[mi - 1], self._data.menus[mi] = (
                self._data.menus[mi], self._data.menus[mi - 1]
            )
            self._rebuild_tree()
            # Re-select the moved menu
            for i, e in enumerate(self._tree_entries):
                if e == (mi - 1, None):
                    self._tree_list._selected_index = i
                    break
        else:
            # Move item up within its menu
            items = self._data.menus[mi].items
            if ii <= 0:
                return
            items[ii - 1], items[ii] = items[ii], items[ii - 1]
            self._rebuild_tree()
            for i, e in enumerate(self._tree_entries):
                if e == (mi, ii - 1):
                    self._tree_list._selected_index = i
                    break
        self._update_properties()

    def _move_down(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        mi, ii = entry
        if ii is None:
            # Move menu down
            if mi >= len(self._data.menus) - 1:
                return
            self._data.menus[mi], self._data.menus[mi + 1] = (
                self._data.menus[mi + 1], self._data.menus[mi]
            )
            self._rebuild_tree()
            for i, e in enumerate(self._tree_entries):
                if e == (mi + 1, None):
                    self._tree_list._selected_index = i
                    break
        else:
            items = self._data.menus[mi].items
            if ii >= len(items) - 1:
                return
            items[ii], items[ii + 1] = items[ii + 1], items[ii]
            self._rebuild_tree()
            for i, e in enumerate(self._tree_entries):
                if e == (mi, ii + 1):
                    self._tree_list._selected_index = i
                    break
        self._update_properties()

    # ------------------------------------------------------------------
    # OK / Cancel
    # ------------------------------------------------------------------

    def _on_ok(self) -> None:
        self.close(self._data)

    def _on_cancel(self) -> None:
        self.close(None)

    # ------------------------------------------------------------------
    # Layout — position child widgets for hit-testing
    # ------------------------------------------------------------------

    def _layout_children(self) -> None:
        """Position all child widgets based on current _screen_rect.

        Called from both arrange() and paint() so that _screen_rect values
        are always up-to-date for hit-testing and rendering.
        """
        sr = self._screen_rect
        if sr.width == 0 and sr.height == 0:
            return

        # --- Left side: tree list ---
        tree_x = sr.x + 2
        tree_y = sr.y + 2
        self._tree_list._screen_rect = Rect(tree_x, tree_y, 28, 12)

        # --- Left side: action buttons ---
        btn_y = sr.y + 15
        bx = sr.x + 2
        self._btn_add_menu._screen_rect = Rect(bx, btn_y, 7, 1)
        bx += 8
        self._btn_add_item._screen_rect = Rect(bx, btn_y, 7, 1)
        bx += 8
        self._btn_add_sep._screen_rect = Rect(bx, btn_y, 6, 1)

        btn_y2 = sr.y + 16
        bx = sr.x + 2
        self._btn_delete._screen_rect = Rect(bx, btn_y2, 8, 1)
        bx += 9
        self._btn_up._screen_rect = Rect(bx, btn_y2, 6, 1)
        bx += 7
        self._btn_down._screen_rect = Rect(bx, btn_y2, 6, 1)

        # --- Right side: properties ---
        prop_x = sr.x + 33
        prop_label_x = prop_x
        prop_input_x = prop_x + 10
        prop_input_w = 18

        # Hide all property widgets first, then show based on mode
        offscreen = Rect(-1, -1, 0, 0)
        for w in (self._lbl_label, self._inp_label,
                  self._lbl_shortcut, self._inp_shortcut,
                  self._lbl_handler, self._inp_handler,
                  self._lbl_enabled, self._chk_enabled):
            w._screen_rect = offscreen

        if self._prop_mode == "menu":
            py = sr.y + 3
            self._lbl_label._screen_rect = Rect(prop_label_x, py, 9, 1)
            self._inp_label._screen_rect = Rect(prop_input_x, py, prop_input_w, 1)
        elif self._prop_mode == "item":
            py = sr.y + 3
            self._lbl_label._screen_rect = Rect(prop_label_x, py, 9, 1)
            self._inp_label._screen_rect = Rect(prop_input_x, py, prop_input_w, 1)
            py += 2
            self._lbl_shortcut._screen_rect = Rect(prop_label_x, py, 9, 1)
            self._inp_shortcut._screen_rect = Rect(prop_input_x, py, prop_input_w, 1)
            py += 2
            self._lbl_handler._screen_rect = Rect(prop_label_x, py, 9, 1)
            self._inp_handler._screen_rect = Rect(prop_input_x, py, prop_input_w, 1)
            py += 2
            self._lbl_enabled._screen_rect = Rect(prop_label_x, py, 9, 1)
            self._chk_enabled._screen_rect = Rect(prop_input_x, py, 4, 1)

        # --- OK / Cancel buttons ---
        ok_x = sr.x + sr.width - 24
        cancel_x = sr.x + sr.width - 13
        btn_y_bottom = sr.y + sr.height - 2
        self._btn_ok._screen_rect = Rect(ok_x, btn_y_bottom, 10, 1)
        self._btn_cancel._screen_rect = Rect(cancel_x, btn_y_bottom, 10, 1)

    def arrange(self, rect: Rect) -> None:
        self._screen_rect = rect
        self.x = rect.x
        self.y = rect.y
        self.width = rect.width
        self.height = rect.height
        self._layout_children()

    # ------------------------------------------------------------------
    # Paint — render child widgets and decorations
    # ------------------------------------------------------------------

    def paint(self, painter: Painter) -> None:
        # Draw dialog chrome (border, title, shadow)
        super().paint(painter)

        # Ensure child positions are up-to-date
        self._layout_children()

        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("dialog.bg", Color.BRIGHT_BLACK)
        fg = self.theme_color("dialog.fg", Color.BLACK)

        # --- Left side: tree list ---
        self._tree_list.paint(painter)

        # --- Left side: action buttons ---
        self._btn_add_menu.paint(painter)
        self._btn_add_item.paint(painter)
        self._btn_add_sep.paint(painter)
        self._btn_delete.paint(painter)
        self._btn_up.paint(painter)
        self._btn_down.paint(painter)

        # --- Vertical separator ---
        sep_x = lx + 31
        for row in range(2, sr.height - 3):
            painter.put_char(sep_x, ly + row, "\u2502", fg=fg, bg=bg)

        # --- Right side: properties ---
        prop_label_x = sr.x + 33

        if self._prop_mode == "menu":
            py = sr.y + 3
            self._lbl_label.paint(painter)
            self._inp_label.paint(painter)
            painter.put_str(prop_label_x - painter._offset.x, py + 2 - painter._offset.y,
                           "(Menu title)", fg=fg, bg=bg)
        elif self._prop_mode == "item":
            self._lbl_label.paint(painter)
            self._inp_label.paint(painter)
            self._lbl_shortcut.paint(painter)
            self._inp_shortcut.paint(painter)
            self._lbl_handler.paint(painter)
            self._inp_handler.paint(painter)
            self._lbl_enabled.paint(painter)
            self._chk_enabled.paint(painter)
        elif self._prop_mode == "separator":
            painter.put_str(prop_label_x - painter._offset.x, sr.y + 4 - painter._offset.y,
                           "(Separator)", fg=fg, bg=bg)
        else:
            painter.put_str(prop_label_x - painter._offset.x, sr.y + 4 - painter._offset.y,
                           "(No selection)", fg=fg, bg=bg)

        # --- OK / Cancel buttons ---
        self._btn_ok.paint(painter)
        self._btn_cancel.paint(painter)

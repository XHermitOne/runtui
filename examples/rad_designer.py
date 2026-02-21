#!/usr/bin/env python3
"""runtui RAD Designer -- Visual form designer for TUI applications.

A Visual Basic / Delphi-style IDE running entirely in the terminal.
Design forms by dragging widgets from the toolbox, edit properties,
save/load as JSON, export as runnable Python, and preview live.
"""

import sys
import os

# Add parent dir to path
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtui import (
    App, Window, Label, Button, TextInput, ListBox,
    MenuBar, Menu, MenuItem, MessageBox, OpenFileDialog, SaveFileDialog,
    Color,
)
from runtui.widgets.container import Container
from runtui.layout.absolute import AbsoluteLayout
from runtui.core.types import Rect
from runtui.rendering.painter import Painter
from runtui.rad.schema import WIDGET_REGISTRY, get_widget_types
from runtui.rad.design_surface import DesignSurface, DesignWidgetInfo
from runtui.rad.serializer import serialize_design, save_json
from runtui.rad.deserializer import load_json, load_design, deserialize_widget, load_menu_data
from runtui.rad.codegen import generate_python, save_python
from runtui.rad.runner import preview_in_app
from runtui.rad.menu_editor import MenuEditorDialog, MenuDesignData


class PropertiesPanel:
    """Manages the properties window, showing editable fields for the selected widget."""

    def __init__(self, window: Window, surface: DesignSurface) -> None:
        self._window = window
        self._surface = surface
        self._content = Container()
        self._content._layout_manager = AbsoluteLayout()
        self._window.set_content(self._content)
        self._current: DesignWidgetInfo | None = None
        self._editors: dict[str, TextInput] = {}

    def show_properties(self, info: DesignWidgetInfo | None) -> None:
        """Rebuild the panel for the given widget (or clear if None)."""
        self._current = info
        self._content.clear_children()
        if self._content._layout_manager and hasattr(self._content._layout_manager, "_original_positions"):
            self._content._layout_manager._original_positions.clear()
        self._editors.clear()

        if not info:
            lbl = Label(text="(no selection)", x=0, y=0, width=22)
            self._content.add_child(lbl)
            return

        typedef = WIDGET_REGISTRY.get(info.widget_type)
        if not typedef:
            return

        panel_w = self._window.width - 4
        val_x = 9
        val_w = max(8, panel_w - val_x - 1)
        y = 0

        # Widget type header
        hdr = Label(text=f"[{info.widget_type}]", x=0, y=y, width=panel_w, bold=True)
        self._content.add_child(hdr)
        y += 1

        # ID field
        lbl = Label(text="id:", x=0, y=y, width=8)
        inp = TextInput(text=info.widget_id, x=val_x, y=y, width=val_w,
                        on_change=lambda v: self._on_id_changed(v))
        self._content.add_child(lbl)
        self._content.add_child(inp)
        self._editors["id"] = inp
        y += 1

        # Type-specific properties
        for pdef in typedef.properties:
            lbl = Label(text=f"{pdef.name}:", x=0, y=y, width=8)
            val = self._read_prop(info, pdef.name)
            inp = TextInput(
                text=str(val) if val is not None else "",
                x=val_x, y=y, width=val_w,
                on_change=lambda v, pn=pdef.name, pt=pdef.prop_type: self._on_prop_changed(pn, pt, v),
            )
            self._content.add_child(lbl)
            self._content.add_child(inp)
            self._editors[pdef.name] = inp
            y += 1

        # Events section
        if typedef.events:
            y += 1
            sep = Label(text="── Events ──", x=0, y=y, width=panel_w, bold=True)
            self._content.add_child(sep)
            y += 1
            for event_name in typedef.events:
                lbl = Label(text=f"{event_name}:", x=0, y=y, width=val_x)
                handler = info.events.get(event_name, "")
                inp = TextInput(
                    text=handler, x=val_x, y=y, width=val_w,
                    on_change=lambda v, en=event_name: self._on_event_changed(en, v),
                )
                self._content.add_child(lbl)
                self._content.add_child(inp)
                y += 1

    def refresh_position(self) -> None:
        """Refresh position fields after a drag without full rebuild."""
        if not self._current:
            return
        orig = self._surface._get_original_pos(self._current.widget)
        if orig:
            ox, oy, ow, oh = orig
            for name, val in [("x", ox), ("y", oy), ("width", ow), ("height", oh)]:
                if name in self._editors:
                    self._editors[name]._text = str(val)
                    self._editors[name]._cursor_pos = len(str(val))
                    self._editors[name].invalidate()

    def _read_prop(self, info: DesignWidgetInfo, prop_name: str) -> object:
        """Read a property value, preferring AbsoluteLayout cache for position."""
        if prop_name in ("x", "y", "width", "height"):
            orig = self._surface._get_original_pos(info.widget)
            if orig:
                mapping = {"x": orig[0], "y": orig[1], "width": orig[2], "height": orig[3]}
                return mapping[prop_name]
        from runtui.rad.serializer import _get_prop_value
        return _get_prop_value(info.widget, prop_name)

    def _on_id_changed(self, value: str) -> None:
        if self._current:
            self._current.widget_id = value

    def _on_prop_changed(self, prop_name: str, prop_type: str, value_str: str) -> None:
        if not self._current:
            return
        try:
            if prop_type == "int":
                typed_val = int(value_str)
            elif prop_type == "float":
                typed_val = float(value_str)
            elif prop_type == "bool":
                typed_val = value_str.lower() in ("true", "1", "yes")
            elif prop_type == "list[str]":
                typed_val = [s.strip() for s in value_str.split(",") if s.strip()]
            else:
                typed_val = value_str
        except (ValueError, TypeError):
            return

        widget = self._current.widget

        # Apply position/size through AbsoluteLayout
        if prop_name in ("x", "y", "width", "height"):
            orig = self._surface._get_original_pos(widget)
            if orig:
                ox, oy, ow, oh = orig
                if prop_name == "x":
                    ox = typed_val
                elif prop_name == "y":
                    oy = typed_val
                elif prop_name == "width":
                    ow = typed_val
                elif prop_name == "height":
                    oh = typed_val
                layout = self._surface._layout_manager
                if layout and hasattr(layout, "_original_positions"):
                    layout._original_positions[id(widget)] = (ox, oy, ow, oh)
                self._surface.invalidate_layout()
            return

        # Apply content properties
        try:
            if prop_name == "filepath" and hasattr(widget, "load"):
                # Image widgets: set filepath and attempt to load the image
                widget._filepath = typed_val
                if typed_val:
                    widget.load(typed_val)
                widget.invalidate()
            elif prop_name == "text" and hasattr(widget, "_text"):
                widget._text = typed_val
            elif prop_name == "items" and hasattr(widget, "_items"):
                widget._items = typed_val
            elif prop_name == "label" and hasattr(widget, "label"):
                widget.label = typed_val
            elif prop_name == "checked" and hasattr(widget, "_checked"):
                widget._checked = typed_val
            else:
                setattr(widget, prop_name, typed_val)
            widget.invalidate()
        except (AttributeError, TypeError):
            pass

    def _on_event_changed(self, event_name: str, handler_name: str) -> None:
        if self._current:
            if handler_name:
                self._current.events[event_name] = handler_name
            else:
                self._current.events.pop(event_name, None)


class RADDesignerApp(App):
    """Visual RAD Designer for runtui applications."""

    def __init__(self) -> None:
        super().__init__(theme="light")
        self._current_file: str | None = None
        self._design_theme = "light"
        self._design_title = "My Application"
        self._menu_design_data = MenuDesignData()

    def on_ready(self) -> None:
        self._setup_menu()
        self._create_toolbox()
        self._create_canvas()
        self._create_properties()

    def _setup_menu(self) -> None:
        menu = MenuBar(menus=[
            Menu("File", [
                MenuItem("New", shortcut="Ctrl+N", action=self._new_design),
                MenuItem("Open...", shortcut="Ctrl+O", action=self._open_design),
                MenuItem("Save", shortcut="Ctrl+S", action=self._save_design),
                MenuItem("Save As...", action=self._save_design_as),
                MenuItem.separator(),
                MenuItem("Export Python...", action=self._export_python),
                MenuItem.separator(),
                MenuItem("Exit", shortcut="Ctrl+Q", action=self.quit),
            ]),
            Menu("Edit", [
                MenuItem("Delete Widget", action=self._delete_widget),
                MenuItem("Duplicate", action=self._duplicate_widget),
                MenuItem.separator(),
                MenuItem("Edit Menus...", action=self._edit_menus),
            ]),
            Menu("Run", [
                MenuItem("Preview (F5)", action=self._preview),
            ]),
            Menu("Theme", [
                MenuItem("Turbo Vision", action=lambda: self._set_design_theme("turbo_vision")),
                MenuItem("Dark", action=lambda: self._set_design_theme("dark")),
                MenuItem("Light", action=lambda: self._set_design_theme("light")),
                MenuItem("Nord", action=lambda: self._set_design_theme("nord")),
                MenuItem("Solarized", action=lambda: self._set_design_theme("solarized")),
            ]),
            Menu("Help", [
                MenuItem("About", action=self._show_about),
            ]),
        ])
        self.set_menu(menu)

    def _create_toolbox(self) -> None:
        self._toolbox_win = Window(
            title="Toolbox",
            x=0, y=1, width=20, height=22,
            resizable=True, closable=False, minimizable=False, maximizable=False,
        )
        content = Container()
        content._layout_manager = AbsoluteLayout()

        # Build toolbox items from registry
        items = []
        self._tool_names: list[str] = []
        for name in get_widget_types():
            typedef = WIDGET_REGISTRY[name]
            items.append(f"{typedef.icon} {name}")
            self._tool_names.append(name)

        self._toolbox_list = ListBox(
            items=items,
            x=0, y=0,
            width=16, height=18,
            on_activate=self._on_tool_activated,
        )
        content.add_child(self._toolbox_list)
        self._toolbox_win.set_content(content)
        self.add_window(self._toolbox_win)

    def _create_canvas(self) -> None:
        self._canvas_win = Window(
            title="Form Designer [untitled]",
            x=21, y=1, width=48, height=24,
            resizable=True,
        )
        self._surface = DesignSurface()
        self._surface.on_selection_changed = self._on_selection_changed
        self._surface.on_widget_moved = self._on_widget_moved
        self._canvas_win.set_content(self._surface)
        self.add_window(self._canvas_win)

    def _create_properties(self) -> None:
        self._props_win = Window(
            title="Properties",
            x=70, y=1, width=28, height=24,
            resizable=True, closable=False, minimizable=False, maximizable=False,
        )
        self._properties = PropertiesPanel(self._props_win, self._surface)
        self.add_window(self._props_win)

    # --- Paint override to add selection overlay ---

    def _paint(self) -> None:
        super()._paint()
        # Paint selection highlight clipped to the canvas window so it
        # does not bleed on top of preview windows or other windows.
        if (self._screen and self._surface.selected
                and self._window_manager
                and self._window_manager.active_window is self._canvas_win):
            buf = self._screen.back
            clip = self._canvas_win.content_rect
            from runtui.core.types import Point
            painter = Painter(buf, clip, offset=Point(0, 0))
            self._surface.paint_selection_overlay(painter)
            # Re-paint mouse cursor on top
            self._mouse_cursor.paint(buf)

    # --- Toolbox callbacks ---

    def _on_tool_activated(self, idx: int, item: str) -> None:
        """Double-click on a tool: set as active tool for placement."""
        if 0 <= idx < len(self._tool_names):
            tool_name = self._tool_names[idx]
            self._surface.active_tool = tool_name
            self._canvas_win.title = f"Form Designer [Click to place {tool_name}]"
            self._needs_repaint = True

    # --- Selection callbacks ---

    def _on_selection_changed(self, info: DesignWidgetInfo | None) -> None:
        self._properties.show_properties(info)
        if info:
            self._canvas_win.title = f"Form Designer [{info.widget_id}]"
        else:
            fname = os.path.basename(self._current_file) if self._current_file else "untitled"
            self._canvas_win.title = f"Form Designer [{fname}]"
        self._needs_repaint = True

    def _on_widget_moved(self, info: DesignWidgetInfo) -> None:
        self._properties.refresh_position()
        self._needs_repaint = True

    # --- File operations ---

    def _get_app_settings(self) -> dict:
        return {
            "theme": self._design_theme,
            "title": self._design_title,
            "window_width": self._canvas_win.width - 2,
            "window_height": self._canvas_win.height - 2,
        }

    def _new_design(self) -> None:
        self._surface.clear_all()
        self._current_file = None
        self._menu_design_data = MenuDesignData()
        self._canvas_win.title = "Form Designer [untitled]"
        self._properties.show_properties(None)
        self._needs_repaint = True

    def _open_design(self) -> None:
        dialog = OpenFileDialog(title="Open Design")
        dialog.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        self.root.add_child(dialog)
        # Store reference to check result on close
        self._pending_open_dialog = dialog
        self._check_dialog_result(dialog, self._finish_open)

    def _finish_open(self, path: str) -> None:
        if not path or not path.endswith(".json"):
            return
        try:
            data = load_json(path)
        except Exception:
            return
        self._surface.clear_all()
        # Load app settings
        app_cfg = data.get("app", {})
        self._design_theme = app_cfg.get("theme", "light")
        self._design_title = app_cfg.get("title", "My Application")

        # Load widgets into the surface
        window_descs = load_design(data)
        for desc in window_descs:
            for widget, w_data in desc["widgets"]:
                widget.can_focus = False
                self._surface.add_child(widget)
                info = DesignWidgetInfo(
                    widget=widget,
                    widget_type=w_data["type"],
                    widget_id=w_data.get("id", ""),
                    events=dict(w_data.get("events", {})),
                )
                self._surface._design_widgets.append(info)
                # Update ID counter
                prefix = self._surface._generate_id(w_data["type"])  # side effect: bumps counter

        # Load menu data
        menu_data = load_menu_data(data)
        self._menu_design_data = menu_data if menu_data else MenuDesignData()

        self._current_file = path
        self._canvas_win.title = f"Form Designer [{os.path.basename(path)}]"
        self._needs_repaint = True

    def _save_design(self) -> None:
        if self._current_file:
            data = serialize_design(self._surface, self._get_app_settings(), self._menu_design_data)
            save_json(data, self._current_file)
        else:
            self._save_design_as()

    def _save_design_as(self) -> None:
        dialog = SaveFileDialog(title="Save Design", default_name="design.json")
        dialog.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        self.root.add_child(dialog)
        self._check_dialog_result(dialog, self._finish_save)

    def _finish_save(self, path: str) -> None:
        if not path:
            return
        if not path.endswith(".json"):
            path += ".json"
        data = serialize_design(self._surface, self._get_app_settings(), self._menu_design_data)
        save_json(data, path)
        self._current_file = path
        self._canvas_win.title = f"Form Designer [{os.path.basename(path)}]"

    def _export_python(self) -> None:
        dialog = SaveFileDialog(title="Export Python", default_name="my_app.py")
        dialog.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        self.root.add_child(dialog)
        self._check_dialog_result(dialog, self._finish_export)

    def _finish_export(self, path: str) -> None:
        if not path:
            return
        if not path.endswith(".py"):
            path += ".py"
        data = serialize_design(self._surface, self._get_app_settings(), self._menu_design_data)
        code = generate_python(data)
        save_python(code, path)

    def _check_dialog_result(self, dialog, callback) -> None:
        """Poll a dialog for closure and invoke callback with result."""
        def _poll():
            if dialog.closed:
                if dialog.result:
                    callback(dialog.result)
                self._needs_repaint = True
            else:
                self.call_later(0.1, _poll)
        self.call_later(0.1, _poll)

    # --- Edit operations ---

    def _delete_widget(self) -> None:
        self._surface.remove_selected()
        self._needs_repaint = True

    def _duplicate_widget(self) -> None:
        self._surface.duplicate_selected()
        self._needs_repaint = True

    def _edit_menus(self) -> None:
        dialog = MenuEditorDialog(data=self._menu_design_data)
        dialog.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        self.root.add_child(dialog)
        self._check_dialog_result(dialog, self._finish_edit_menus)

    def _finish_edit_menus(self, result) -> None:
        if result is not None:
            self._menu_design_data = result

    # --- Run / Preview ---

    def _preview(self) -> None:
        data = serialize_design(self._surface, self._get_app_settings(), self._menu_design_data)
        preview_windows = preview_in_app(data, self)

        def _restore_menu():
            """Restore the designer menu bar when the preview window is closed."""
            self._setup_menu()
            self._needs_repaint = True

        for win in preview_windows:
            win._on_close = _restore_menu

    # --- Theme ---

    def _set_design_theme(self, theme: str) -> None:
        self._design_theme = theme
        self.set_theme(theme)

    # --- Help ---

    def _show_about(self) -> None:
        mb = MessageBox(
            title="About RAD Designer",
            message=(
                "runtui RAD Designer\n"
                "Version 0.1.0\n"
                "\n"
                "Visual form designer for\n"
                "runtui TUI applications.\n"
                "\n"
                "Double-click a widget in the\n"
                "Toolbox to place it on canvas.\n"
                "Click to select, drag to move.\n"
                "Edit properties on the right."
            ),
            buttons=["OK"],
        )
        mb.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        self.root.add_child(mb)
        mb.invalidate()


if __name__ == "__main__":
    app = RADDesignerApp()
    app.run()

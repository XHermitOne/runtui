#!/usr/bin/env python3
"""Demo application showcasing all runtui widgets."""

import datetime
import sys
import os

# Add parent dir to path
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import runtui
from runtui import (
    App, Window, Label, Button, TextInput, PasswordInput,
    Checkbox, RadioButton, RadioGroup, TextArea, ListBox, DropDownList,
    Calendar, ColorPicker, ProgressBar, TerminalWidget, VScrollbar,
    MenuBar, Menu, MenuItem, MessageBox, OpenFileDialog, SaveFileDialog,
    FormDialog, FormField, Color,
)


class DemoApp(App):
    """Showcase application for all runtui widgets."""

    def __init__(self) -> None:
        super().__init__(theme="light")

    def on_ready(self) -> None:
        # Set up menu bar
        self._setup_menu()

        # Create demo windows
        self._create_input_demo()
        self._create_list_demo()
        self._create_calendar_demo()
        self._create_editor_demo()

    def _setup_menu(self) -> None:
        menu = MenuBar(menus=[
            Menu("File", [
                MenuItem("New Window", shortcut="Ctrl+N", action=self._new_window),
                MenuItem("Open...", shortcut="Ctrl+O", action=self._show_open_dialog),
                MenuItem("Save As...", shortcut="Ctrl+S", action=self._show_save_dialog),
                MenuItem.separator(),
                MenuItem("Exit", shortcut="Ctrl+Q", action=self.quit),
            ]),
            Menu("Windows", [
                MenuItem("Cascade", action=self._cascade),
                MenuItem("Tile Horizontal", action=self._tile_h),
                MenuItem("Tile Vertical", action=self._tile_v),
            ]),
            Menu("Theme", [
                MenuItem("Turbo Vision", action=lambda: self.set_theme("turbo_vision")),
                MenuItem("Dark", action=lambda: self.set_theme("dark")),
                MenuItem("Light", action=lambda: self.set_theme("light")),
                MenuItem("Nord", action=lambda: self.set_theme("nord")),
                MenuItem("Solarized", action=lambda: self.set_theme("solarized")),
            ]),
            Menu("Help", [
                MenuItem("About", action=self._show_about),
            ]),
        ])
        self.set_menu(menu)

    def _create_input_demo(self) -> None:
        win = Window(title="Input Widgets", x=2, y=2, width=38, height=18)

        # Build content using absolute positioning
        from runtui.widgets.container import Container
        from runtui.layout.absolute import AbsoluteLayout

        content = Container()
        content._layout_manager = AbsoluteLayout()

        # Text input
        lbl1 = Label(text="Name:", x=1, y=0, width=10)
        inp1 = TextInput(text="John Doe", x=11, y=0, width=22, id="name_input")
        content.add_child(lbl1)
        content.add_child(inp1)

        # Password
        lbl2 = Label(text="Password:", x=1, y=2, width=10)
        inp2 = PasswordInput(x=11, y=2, width=22)
        content.add_child(lbl2)
        content.add_child(inp2)

        # Checkboxes
        cb1 = Checkbox(label="Bold", x=1, y=4, width=15)
        cb2 = Checkbox(label="Italic", x=17, y=4, width=15)
        content.add_child(cb1)
        content.add_child(cb2)

        # Radio buttons
        group = RadioGroup()
        r1 = RadioButton(label="Option A", x=1, y=6, width=15, group=group, selected=True)
        r2 = RadioButton(label="Option B", x=1, y=7, width=15, group=group)
        r3 = RadioButton(label="Option C", x=1, y=8, width=15, group=group)
        content.add_child(r1)
        content.add_child(r2)
        content.add_child(r3)

        # Dropdown
        lbl3 = Label(text="Color:", x=1, y=10, width=10)
        dd = DropDownList(items=["Red", "Green", "Blue", "Yellow", "Cyan", "Magenta"],
                         x=11, y=10, width=22)
        content.add_child(lbl3)
        content.add_child(dd)

        # Progress bar
        lbl4 = Label(text="Progress:", x=1, y=12, width=10)
        pb = ProgressBar(value=65, max_value=100, x=11, y=12, width=22)
        content.add_child(lbl4)
        content.add_child(pb)

        # Buttons
        btn1 = Button(text="OK", x=5, y=14, width=12,
                      on_click=lambda: self._show_about())
        btn2 = Button(text="Cancel", x=19, y=14, width=12,
                      on_click=lambda: None)
        content.add_child(btn1)
        content.add_child(btn2)

        win.set_content(content)
        self.add_window(win)

    def _create_list_demo(self) -> None:
        win = Window(title="List Demo", x=42, y=2, width=32, height=14)

        from runtui.widgets.container import Container
        from runtui.layout.absolute import AbsoluteLayout

        content = Container()
        content._layout_manager = AbsoluteLayout()

        items = [f"Item {i+1}: {'★' if i % 3 == 0 else '○'} Sample entry" for i in range(20)]
        lb = ListBox(items=items, x=0, y=0, width=28, height=10)
        content.add_child(lb)

        lbl = Label(text="20 items", x=0, y=11, width=28, align="center")
        content.add_child(lbl)

        win.set_content(content)
        self.add_window(win)

    def _create_calendar_demo(self) -> None:
        win = Window(title="Calendar", x=42, y=16, width=26, height=13)

        cal = Calendar(
            selected=datetime.date.today(),
            on_select=lambda d: None,
        )
        win.set_content(cal)
        self.add_window(win)

    def _create_editor_demo(self) -> None:
        win = Window(title="Text Editor", x=2, y=20, width=38, height=12)

        sample_text = (
            "# Welcome to runtui!\n"
            "\n"
            "This is a multi-line text editor.\n"
            "It supports:\n"
            "  - Arrow key navigation\n"
            "  - Backspace and Delete\n"
            "  - Home/End/PgUp/PgDn\n"
            "  - Undo (Ctrl+Z)\n"
            "  - Mouse click positioning\n"
            "  - Scroll wheel support\n"
            "\n"
            "Try editing this text!"
        )
        ta = TextArea(text=sample_text, width=34, height=8)
        win.set_content(ta)
        self.add_window(win)

    def _new_window(self) -> None:
        count = len(self._window_manager.windows) + 1 if self._window_manager else 1
        win = Window(title=f"Window {count}", width=30, height=10)
        lbl = Label(text=f"This is window #{count}", x=2, y=2)
        from runtui.widgets.container import Container
        content = Container()
        content.add_child(lbl)
        win.set_content(content)
        self.add_window(win)

    def _cascade(self) -> None:
        if self._window_manager:
            self._window_manager.cascade()
            self.invalidate_all()

    def _tile_h(self) -> None:
        if self._window_manager:
            self._window_manager.tile_horizontal()
            self.invalidate_all()

    def _tile_v(self) -> None:
        if self._window_manager:
            self._window_manager.tile_vertical()
            self.invalidate_all()

    def _show_open_dialog(self) -> None:
        # In a real app, this would be shown modally
        dialog = OpenFileDialog(title="Open File")
        dialog.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        # Add as a window for demo purposes
        self.root.add_child(dialog)
        dialog.invalidate()

    def _show_save_dialog(self) -> None:
        dialog = SaveFileDialog(title="Save File", default_name="untitled.txt")
        dialog.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        self.root.add_child(dialog)
        dialog.invalidate()

    def _show_about(self) -> None:
        mb = MessageBox(
            title="About runtui",
            message=(
                "runtui - Terminal UI Framework\n"
                "Version 0.1.0\n"
                "\n"
                "A from-scratch TUI framework\n"
                "for Python 3.12+\n"
                "\n"
                "Features: Windows, Menus, Dialogs,\n"
                "Input widgets, Themes, Mouse support"
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
    app = DemoApp()
    app.run()

#!/usr/bin/env python3
"""Demo application showcasing all runtui widgets."""

import datetime
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import runtui
from runtui import (
    App, Window, Label, Button, TextInput, PasswordInput,
    Checkbox, RadioButton, RadioGroup, TextArea, ListBox, DropDownList,
    Calendar, ColorPicker, ProgressBar, TerminalWidget, VScrollbar,
    MenuBar, Menu, MenuItem, MessageBox, OpenFileDialog, SaveFileDialog,
    FormDialog, FormField, Color,
)


class MyApplicationApp(App):
    """Application: My Application."""

    def __init__(self) -> None:
        super().__init__(theme="light")

    def on_ready(self) -> None:
        win = Window(title="Calendar", x=42, y=16, width=26, height=13)

        cal = Calendar(
            selected=datetime.date.today(),
            on_select=lambda d: None,
        )
        win.set_content(cal)
        self.add_window(win)

if __name__ == "__main__":
    app = MyApplicationApp()
    app.run()
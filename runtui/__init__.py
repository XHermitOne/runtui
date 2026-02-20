"""runtui - A from-scratch Terminal UI Framework for Python 3.12+"""

__version__ = "0.1.0"

# Core types
from .core.types import Point, Size, Rect, Color, Attrs, Cell, BorderStyle, ColorDepth
from .core.keys import Keys, Modifiers, MouseButton, MouseAction
from .core.event import (
    Event, KeyEvent, MouseEvent, FocusEvent, WindowEvent, ResizeEvent,
    ThemeChangedEvent, CustomEvent, WindowAction, Phase, Strategy,
)
from .core.unicode import char_width, string_width

# Application
from .app import App

# Widgets
from .widgets.base import Widget
from .widgets.container import Container
from .widgets.label import Label
from .widgets.button import Button
from .widgets.input import TextInput
from .widgets.password import PasswordInput
from .widgets.checkbox import Checkbox
from .widgets.radio import RadioButton, RadioGroup
from .widgets.textarea import TextArea
from .widgets.scrollbar import VScrollbar, HScrollbar
from .widgets.listbox import ListBox
from .widgets.dropdown import DropDownList
from .widgets.menu import MenuBar, Menu, MenuItem
from .widgets.context_menu import ContextMenu
from .widgets.calendar import Calendar
from .widgets.color_picker import ColorPicker
from .widgets.terminal import TerminalWidget
from .widgets.terminal_pipe import PipeTerminalWidget
from .widgets.progressbar import ProgressBar
from .widgets.image import ImageWidget
from .widgets.static_image import StaticImage

# Windows
from .windows.window import Window
from .windows.window_manager import WindowManager

# Dialogs
from .dialogs.base import Dialog
from .dialogs.message import MessageBox
from .dialogs.file_open import OpenFileDialog
from .dialogs.file_save import SaveFileDialog
from .dialogs.form import FormDialog, FormField

# Layout
from .layout.absolute import AbsoluteLayout
from .layout.dock import DockLayout
from .layout.box import HBoxLayout, VBoxLayout
from .layout.grid import GridLayout

# Themes
from .themes.engine import ThemeEngine, ThemeDefinition

__all__ = [
    # Core
    "Point", "Size", "Rect", "Color", "Attrs", "Cell", "BorderStyle", "ColorDepth",
    "Keys", "Modifiers", "MouseButton", "MouseAction",
    "Event", "KeyEvent", "MouseEvent", "FocusEvent", "WindowEvent", "ResizeEvent",
    "ThemeChangedEvent", "CustomEvent", "WindowAction", "Phase", "Strategy",
    "char_width", "string_width",
    # App
    "App",
    # Widgets
    "Widget", "Container", "Label", "Button",
    "TextInput", "PasswordInput", "Checkbox", "RadioButton", "RadioGroup",
    "TextArea", "VScrollbar", "HScrollbar", "ListBox", "DropDownList",
    "MenuBar", "Menu", "MenuItem", "ContextMenu",
    "Calendar", "ColorPicker", "TerminalWidget", "PipeTerminalWidget", "ProgressBar", "ImageWidget", "StaticImage",
    # Windows
    "Window", "WindowManager",
    # Dialogs
    "Dialog", "MessageBox", "OpenFileDialog", "SaveFileDialog",
    "FormDialog", "FormField",
    # Layout
    "AbsoluteLayout", "DockLayout", "HBoxLayout", "VBoxLayout", "GridLayout",
    # Themes
    "ThemeEngine", "ThemeDefinition",
]

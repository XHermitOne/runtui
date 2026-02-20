"""Gruvbox Dark theme."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

# Gruvbox Palette
_BG0 = Color.from_hex("#282828")
_BG1 = Color.from_hex("#3c3836")
_BG2 = Color.from_hex("#504945")
_FG0 = Color.from_hex("#fbf1c7")
_FG1 = Color.from_hex("#ebdbb2")
_GRAY = Color.from_hex("#928374")
_RED = Color.from_hex("#cc241d")
_GREEN = Color.from_hex("#98971a")
_YELLOW = Color.from_hex("#d79921")
_BLUE = Color.from_hex("#458588")
_PURPLE = Color.from_hex("#b16286")
_AQUA = Color.from_hex("#689d6a")
_ORANGE = Color.from_hex("#d65d0e")

gruvbox_theme = ThemeDefinition(
    name="gruvbox",
    colors={
        "desktop.bg": _BG0,
        "desktop.fg": _FG1,

        "window.bg": _BG1,
        "window.fg": _FG1,
        "window.border": _GRAY,
        "window.title": _FG1,
        "window.title.bg": _BG1,
        "window.active.border": _ORANGE,
        "window.active.title": _BG0,
        "window.active.title.bg": _ORANGE,
        "window.button": _FG0,
        "window.shadow": _BG0,

        "container.bg": _BG1,
        "container.fg": _FG1,
        "container.border": _GRAY,
        "container.title": _AQUA,

        "label.fg": _FG1,
        "label.bg": _BG1,

        "button.fg": _BG0,
        "button.bg": _BLUE,
        "button.focused.fg": _BG0,
        "button.focused.bg": _YELLOW,
        "button.pressed.fg": _BG0,
        "button.pressed.bg": _RED,

        "input.fg": _FG1,
        "input.bg": _BG2,
        "input.focused.fg": _FG0,
        "input.focused.bg": _BG0,
        "input.cursor": _FG0,
        "input.placeholder": _GRAY,
        "input.selection.fg": _BG0,
        "input.selection.bg": _AQUA,

        "menu.bg": _BG2,
        "menu.fg": _FG1,
        "menu.selected.bg": _ORANGE,
        "menu.selected.fg": _BG0,
        "menu.hotkey": _RED,
        "menu.disabled": _GRAY,

        "checkbox.fg": _FG1,
        "checkbox.bg": _BG1,
        "checkbox.focused.fg": _BG0,
        "checkbox.focused.bg": _YELLOW,

        "scrollbar.track": _BG1,
        "scrollbar.thumb": _GRAY,
        "scrollbar.arrow": _FG1,

        "dialog.bg": _BG1,
        "dialog.fg": _FG1,
        "dialog.border": _AQUA,
        "dialog.title": _FG0,

        "listbox.fg": _FG1,
        "listbox.bg": _BG0,
        "listbox.selected.fg": _BG0,
        "listbox.selected.bg": _ORANGE,

        "dropdown.fg": _FG1,
        "dropdown.bg": _BG2,
        "dropdown.arrow": _FG1,

        "calendar.fg": _FG1,
        "calendar.bg": _BG1,
        "calendar.today": _YELLOW,
        "calendar.selected": _BLUE,
        "calendar.header": _GRAY,

        "taskbar.bg": _BG2,
        "taskbar.fg": _FG1,
        "taskbar.active.bg": _AQUA,
        "taskbar.active.fg": _BG0,
    },
    borders={
        "window": BorderStyle.DOUBLE,
        "dialog": BorderStyle.DOUBLE,
        "container": BorderStyle.SINGLE,
        "input": BorderStyle.SINGLE,
    },
    glyphs={
        "checkbox.checked": "[x]",
        "checkbox.unchecked": "[ ]",
        "radio.selected": "(*)",
        "radio.unselected": "( )",
        "scrollbar.thumb": "▓",
        "scrollbar.track": "░",
        "scrollbar.up": "▲",
        "scrollbar.down": "▼",
        "scrollbar.left": "◄",
        "scrollbar.right": "►",
        "window.close": "[x]",
        "window.maximize": "[^]",
        "window.minimize": "[_]",
        "window.restore": "[+]",
        "menu.arrow": "►",
        "menu.separator": "─",
        "dropdown.arrow": "▼",
        "cursor.arrow": "▲",
        "cursor.hand": "¶",
        "cursor.text": "│",
    },
)
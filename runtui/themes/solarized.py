"""Solarized dark theme."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

# Solarized palette
_BASE03 = Color.from_hex("#002b36")
_BASE02 = Color.from_hex("#073642")
_BASE01 = Color.from_hex("#586e75")
_BASE00 = Color.from_hex("#657b83")
_BASE0 = Color.from_hex("#839496")
_BASE1 = Color.from_hex("#93a1a1")
_BASE2 = Color.from_hex("#eee8d5")
_BASE3 = Color.from_hex("#fdf6e3")
_YELLOW = Color.from_hex("#b58900")
_ORANGE = Color.from_hex("#cb4b16")
_RED = Color.from_hex("#dc322f")
_MAGENTA = Color.from_hex("#d33682")
_VIOLET = Color.from_hex("#6c71c4")
_BLUE = Color.from_hex("#268bd2")
_CYAN = Color.from_hex("#2aa198")
_GREEN = Color.from_hex("#859900")

NAME = "solarized"

solarized_theme = ThemeDefinition(
    name=NAME,
    colors={
        "desktop.bg": _BASE03,
        "desktop.fg": _BASE02,

        "window.bg": _BASE02,
        "window.fg": _BASE0,
        "window.border": _BASE01,
        "window.title": _BASE1,
        "window.title.bg": _BASE02,
        "window.active.border": _BLUE,
        "window.active.title": _BASE2,
        "window.active.title.bg": _BLUE,
        "window.button": _BASE0,
        "window.shadow": _BASE03,

        "container.bg": _BASE02,
        "container.fg": _BASE0,
        "container.border": _BASE01,
        "container.title": _BASE1,

        "label.fg": _BASE0,
        "label.bg": _BASE02,

        "button.fg": _BASE03,
        "button.bg": _CYAN,
        "button.focused.fg": _BASE03,
        "button.focused.bg": _GREEN,
        "button.pressed.fg": _BASE03,
        "button.pressed.bg": _BLUE,

        "input.fg": _BASE0,
        "input.bg": _BASE03,
        "input.focused.fg": _BASE1,
        "input.focused.bg": _BASE02,
        "input.cursor": _BASE1,
        "input.placeholder": _BASE01,
        "input.selection.fg": _BASE03,
        "input.selection.bg": _CYAN,

        "menu.bg": _BASE02,
        "menu.fg": _BASE0,
        "menu.selected.bg": _BLUE,
        "menu.selected.fg": _BASE2,
        "menu.hotkey": _ORANGE,
        "menu.disabled": _BASE01,

        "checkbox.fg": _BASE0,
        "checkbox.bg": _BASE02,
        "checkbox.focused.fg": _BASE2,
        "checkbox.focused.bg": _BLUE,

        "scrollbar.track": _BASE02,
        "scrollbar.thumb": _BASE01,
        "scrollbar.arrow": _BASE0,

        "dialog.bg": _BASE02,
        "dialog.fg": _BASE0,
        "dialog.border": _BLUE,
        "dialog.title": _BASE2,

        "listbox.fg": _BASE0,
        "listbox.bg": _BASE03,
        "listbox.selected.fg": _BASE2,
        "listbox.selected.bg": _BLUE,

        "dropdown.fg": _BASE0,
        "dropdown.bg": _BASE02,
        "dropdown.arrow": _BASE0,

        "calendar.fg": _BASE0,
        "calendar.bg": _BASE02,
        "calendar.today": _YELLOW,
        "calendar.selected": _CYAN,
        "calendar.header": _BLUE,

        "taskbar.bg": _BASE03,
        "taskbar.fg": _BASE0,
        "taskbar.active.bg": _BLUE,
        "taskbar.active.fg": _BASE2,
    },
    borders={
        "window": BorderStyle.SINGLE,
        "dialog": BorderStyle.DOUBLE,
        "container": BorderStyle.SINGLE,
        "input": BorderStyle.SINGLE,
    },
    glyphs={
        "checkbox.checked": "[✓]",
        "checkbox.unchecked": "[ ]",
        "radio.selected": "(●)",
        "radio.unselected": "(○)",
        "scrollbar.thumb": "█",
        "scrollbar.track": "░",
        "scrollbar.up": "▲",
        "scrollbar.down": "▼",
        "scrollbar.left": "◄",
        "scrollbar.right": "►",
        "window.close": "[×]",
        "window.maximize": "[□]",
        "window.minimize": "[_]",
        "window.restore": "[❐]",
        "menu.arrow": "›",
        "menu.separator": "─",
        "dropdown.arrow": "▾",
        "cursor.arrow": "▶",
        "cursor.hand": "☞",
        "cursor.text": "│",
    },
)

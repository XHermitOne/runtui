"""Nord color scheme theme."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

# Nord palette
_NORD0 = Color.from_hex("#2E3440")   # Polar Night
_NORD1 = Color.from_hex("#3B4252")
_NORD2 = Color.from_hex("#434C5E")
_NORD3 = Color.from_hex("#4C566A")
_NORD4 = Color.from_hex("#D8DEE9")   # Snow Storm
_NORD5 = Color.from_hex("#E5E9F0")
_NORD6 = Color.from_hex("#ECEFF4")
_NORD7 = Color.from_hex("#8FBCBB")   # Frost
_NORD8 = Color.from_hex("#88C0D0")
_NORD9 = Color.from_hex("#81A1C1")
_NORD10 = Color.from_hex("#5E81AC")
_NORD11 = Color.from_hex("#BF616A")  # Aurora
_NORD12 = Color.from_hex("#D08770")
_NORD13 = Color.from_hex("#EBCB8B")
_NORD14 = Color.from_hex("#A3BE8C")
_NORD15 = Color.from_hex("#B48EAD")

nord_theme = ThemeDefinition(
    name="nord",
    colors={
        "desktop.bg": _NORD0,
        "desktop.fg": _NORD1,

        "window.bg": _NORD1,
        "window.fg": _NORD4,
        "window.border": _NORD3,
        "window.title": _NORD4,
        "window.title.bg": _NORD1,
        "window.active.border": _NORD8,
        "window.active.title": _NORD6,
        "window.active.title.bg": _NORD10,
        "window.button": _NORD4,
        "window.shadow": _NORD0,

        "container.bg": _NORD1,
        "container.fg": _NORD4,
        "container.border": _NORD3,
        "container.title": _NORD4,

        "label.fg": _NORD4,
        "label.bg": _NORD1,

        "button.fg": _NORD0,
        "button.bg": _NORD8,
        "button.focused.fg": _NORD0,
        "button.focused.bg": _NORD7,
        "button.pressed.fg": _NORD0,
        "button.pressed.bg": _NORD9,

        "input.fg": _NORD4,
        "input.bg": _NORD0,
        "input.focused.fg": _NORD6,
        "input.focused.bg": _NORD2,
        "input.cursor": _NORD4,
        "input.placeholder": _NORD3,
        "input.selection.fg": _NORD0,
        "input.selection.bg": _NORD8,

        "menu.bg": _NORD2,
        "menu.fg": _NORD4,
        "menu.selected.bg": _NORD10,
        "menu.selected.fg": _NORD6,
        "menu.hotkey": _NORD12,
        "menu.disabled": _NORD3,

        "checkbox.fg": _NORD4,
        "checkbox.bg": _NORD1,
        "checkbox.focused.fg": _NORD6,
        "checkbox.focused.bg": _NORD10,

        "scrollbar.track": _NORD2,
        "scrollbar.thumb": _NORD3,
        "scrollbar.arrow": _NORD4,

        "dialog.bg": _NORD2,
        "dialog.fg": _NORD4,
        "dialog.border": _NORD8,
        "dialog.title": _NORD6,

        "listbox.fg": _NORD4,
        "listbox.bg": _NORD0,
        "listbox.selected.fg": _NORD6,
        "listbox.selected.bg": _NORD10,

        "dropdown.fg": _NORD4,
        "dropdown.bg": _NORD1,
        "dropdown.arrow": _NORD4,

        "calendar.fg": _NORD4,
        "calendar.bg": _NORD1,
        "calendar.today": _NORD13,
        "calendar.selected": _NORD10,
        "calendar.header": _NORD8,

        "taskbar.bg": _NORD0,
        "taskbar.fg": _NORD4,
        "taskbar.active.bg": _NORD10,
        "taskbar.active.fg": _NORD6,
    },
    borders={
        "window": BorderStyle.ROUNDED,
        "dialog": BorderStyle.ROUNDED,
        "container": BorderStyle.SINGLE,
        "input": BorderStyle.SINGLE,
    },
    glyphs={
        "checkbox.checked": "[✓]",
        "checkbox.unchecked": "[ ]",
        "radio.selected": "(●)",
        "radio.unselected": "(○)",
        "scrollbar.thumb": "▐",
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

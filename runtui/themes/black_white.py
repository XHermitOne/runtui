"""Black and White Monochrome theme."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

# Grayscale Palette
_BLACK = Color.from_hex("#000000")
_DARK_GRAY = Color.from_hex("#333333")
_MED_GRAY = Color.from_hex("#777777")
_LIGHT_GRAY = Color.from_hex("#cccccc")
_WHITE = Color.from_hex("#ffffff")

NAME = "black_white"

black_white_theme = ThemeDefinition(
    name=NAME,
    colors={
        "desktop.bg": _BLACK,
        "desktop.fg": _LIGHT_GRAY,

        "window.bg": _BLACK,
        "window.fg": _WHITE,
        "window.border": _MED_GRAY,
        "window.title": _LIGHT_GRAY,
        "window.title.bg": _BLACK,
        "window.active.border": _WHITE,
        "window.active.title": _BLACK,
        "window.active.title.bg": _WHITE,
        "window.button": _WHITE,
        "window.shadow": _DARK_GRAY,

        "container.bg": _BLACK,
        "container.fg": _WHITE,
        "container.border": _MED_GRAY,
        "container.title": _WHITE,

        "label.fg": _WHITE,
        "label.bg": _BLACK,

        # Inverted colors for interaction
        "button.fg": _WHITE,
        "button.bg": _DARK_GRAY,
        "button.focused.fg": _BLACK,
        "button.focused.bg": _WHITE,
        "button.pressed.fg": _BLACK,
        "button.pressed.bg": _LIGHT_GRAY,

        "input.fg": _WHITE,
        "input.bg": _DARK_GRAY,
        "input.focused.fg": _BLACK,
        "input.focused.bg": _WHITE,
        "input.cursor": _BLACK,
        "input.placeholder": _MED_GRAY,
        "input.selection.fg": _BLACK,
        "input.selection.bg": _LIGHT_GRAY,

        "menu.bg": _BLACK,
        "menu.fg": _WHITE,
        "menu.selected.bg": _WHITE,
        "menu.selected.fg": _BLACK,
        "menu.hotkey": _LIGHT_GRAY, # Underline/Distinct gray
        "menu.disabled": _MED_GRAY,

        "checkbox.fg": _WHITE,
        "checkbox.bg": _BLACK,
        "checkbox.focused.fg": _BLACK,
        "checkbox.focused.bg": _WHITE,

        "scrollbar.track": _DARK_GRAY,
        "scrollbar.thumb": _LIGHT_GRAY,
        "scrollbar.arrow": _WHITE,

        "dialog.bg": _DARK_GRAY,
        "dialog.fg": _WHITE,
        "dialog.border": _WHITE,
        "dialog.title": _WHITE,

        "listbox.fg": _WHITE,
        "listbox.bg": _BLACK,
        "listbox.selected.fg": _BLACK,
        "listbox.selected.bg": _WHITE,

        "dropdown.fg": _WHITE,
        "dropdown.bg": _DARK_GRAY,
        "dropdown.arrow": _WHITE,

        "calendar.fg": _WHITE,
        "calendar.bg": _BLACK,
        "calendar.today": _MED_GRAY,
        "calendar.selected": _WHITE,
        "calendar.header": _LIGHT_GRAY,

        "taskbar.bg": _DARK_GRAY,
        "taskbar.fg": _WHITE,
        "taskbar.active.bg": _WHITE,
        "taskbar.active.fg": _BLACK,
    },
    borders={
        "window": BorderStyle.SINGLE,
        "dialog": BorderStyle.DOUBLE,
        "container": BorderStyle.SINGLE,
        "input": BorderStyle.SINGLE,
    },
    glyphs={
        "checkbox.checked": "[+]",
        "checkbox.unchecked": "[ ]",
        "radio.selected": "(*)",
        "radio.unselected": "( )",
        "scrollbar.thumb": "▓",
        "scrollbar.track": "░",
        "scrollbar.up": "^",
        "scrollbar.down": "v",
        "scrollbar.left": "<",
        "scrollbar.right": ">",
        "window.close": "X",
        "window.maximize": "O",
        "window.minimize": "_",
        "window.restore": "+",
        "menu.arrow": ">",
        "menu.separator": "-",
        "dropdown.arrow": "v",
        "cursor.arrow": ">",
        "cursor.hand": "+",
        "cursor.text": "I",
    },
)
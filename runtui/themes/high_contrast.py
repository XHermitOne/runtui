"""High Contrast Accessibility theme."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

# HC Palette
_BLACK = Color.from_hex("#000000")
_WHITE = Color.from_hex("#ffffff")
_CYAN = Color.from_hex("#00ffff")
_YELLOW = Color.from_hex("#ffff00")
_GREEN_BRIGHT = Color.from_hex("#00ff00")

high_contrast_theme = ThemeDefinition(
    name="high_contrast",
    colors={
        "desktop.bg": _BLACK,
        "desktop.fg": _WHITE,

        "window.bg": _BLACK,
        "window.fg": _WHITE,
        "window.border": _WHITE,
        "window.title": _YELLOW,
        "window.title.bg": _BLACK,
        "window.active.border": _CYAN,
        "window.active.title": _BLACK,
        "window.active.title.bg": _CYAN,
        "window.button": _WHITE,
        "window.shadow": _WHITE,  # White shadow for visibility against black

        "container.bg": _BLACK,
        "container.fg": _WHITE,
        "container.border": _WHITE,
        "container.title": _YELLOW,

        "label.fg": _WHITE,
        "label.bg": _BLACK,

        "button.fg": _BLACK,
        "button.bg": _WHITE,
        "button.focused.fg": _BLACK,
        "button.focused.bg": _CYAN,
        "button.pressed.fg": _BLACK,
        "button.pressed.bg": _YELLOW,

        "input.fg": _WHITE,
        "input.bg": _BLACK,
        "input.focused.fg": _BLACK,
        "input.focused.bg": _CYAN,
        "input.cursor": _BLACK,
        "input.placeholder": _WHITE,
        "input.selection.fg": _BLACK,
        "input.selection.bg": _YELLOW,

        "menu.bg": _BLACK,
        "menu.fg": _WHITE,
        "menu.selected.bg": _YELLOW,
        "menu.selected.fg": _BLACK,
        "menu.hotkey": _CYAN,
        "menu.disabled": _WHITE,

        "checkbox.fg": _WHITE,
        "checkbox.bg": _BLACK,
        "checkbox.focused.fg": _BLACK,
        "checkbox.focused.bg": _CYAN,

        "scrollbar.track": _BLACK,
        "scrollbar.thumb": _WHITE,
        "scrollbar.arrow": _CYAN,

        "dialog.bg": _BLACK,
        "dialog.fg": _WHITE,
        "dialog.border": _YELLOW,
        "dialog.title": _CYAN,

        "listbox.fg": _WHITE,
        "listbox.bg": _BLACK,
        "listbox.selected.fg": _BLACK,
        "listbox.selected.bg": _CYAN,

        "dropdown.fg": _WHITE,
        "dropdown.bg": _BLACK,
        "dropdown.arrow": _YELLOW,

        "calendar.fg": _WHITE,
        "calendar.bg": _BLACK,
        "calendar.today": _YELLOW,
        "calendar.selected": _CYAN,
        "calendar.header": _WHITE,

        "taskbar.bg": _BLACK,
        "taskbar.fg": _WHITE,
        "taskbar.active.bg": _CYAN,
        "taskbar.active.fg": _BLACK,
    },
    borders={
        "window": BorderStyle.DOUBLE,
        "dialog": BorderStyle.DOUBLE,
        "container": BorderStyle.SINGLE,
        "input": BorderStyle.SINGLE,
    },
    glyphs={
        "checkbox.checked": "[ X ]",
        "checkbox.unchecked": "[   ]",
        "radio.selected": "( @ )",
        "radio.unselected": "(   )",
        "scrollbar.thumb": "█",
        "scrollbar.track": "░",
        "scrollbar.up": "▲",
        "scrollbar.down": "▼",
        "scrollbar.left": "◄",
        "scrollbar.right": "►",
        "window.close": " X ",
        "window.maximize": " □ ",
        "window.minimize": " _ ",
        "window.restore": " R ",
        "menu.arrow": ">>",
        "menu.separator": "=",
        "dropdown.arrow": "V",
        "cursor.arrow": "->",
        "cursor.hand": "H",
        "cursor.text": "I",
    },
)
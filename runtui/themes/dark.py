"""Modern dark theme."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

_BG = Color.from_rgb(30, 30, 30)
_FG = Color.from_rgb(212, 212, 212)
_ACCENT = Color.from_rgb(0, 122, 204)
_ACCENT_LIGHT = Color.from_rgb(55, 148, 220)
_BORDER = Color.from_rgb(60, 60, 60)
_SURFACE = Color.from_rgb(45, 45, 45)
_SURFACE_LIGHT = Color.from_rgb(60, 60, 60)
_WHITE = Color.from_rgb(255, 255, 255)
_BLACK = Color.from_rgb(0, 0, 0)
_RED = Color.from_rgb(244, 67, 54)
_GREEN = Color.from_rgb(76, 175, 80)
_YELLOW = Color.from_rgb(255, 235, 59)
_DIM = Color.from_rgb(100, 100, 100)
_SHADOW = Color.from_rgb(10, 10, 10)

NAME = "dark"

dark_theme = ThemeDefinition(
    name=NAME,
    colors={
        "desktop.bg": Color.from_rgb(20, 20, 20),
        "desktop.fg": Color.from_rgb(40, 40, 40),

        "window.bg": _SURFACE,
        "window.fg": _FG,
        "window.border": _BORDER,
        "window.title": _FG,
        "window.title.bg": _SURFACE,
        "window.active.border": _ACCENT,
        "window.active.title": _WHITE,
        "window.active.title.bg": _ACCENT,
        "window.button": _FG,
        "window.shadow": _SHADOW,

        "container.bg": _SURFACE,
        "container.fg": _FG,
        "container.border": _BORDER,
        "container.title": _FG,

        "label.fg": _FG,
        "label.bg": _SURFACE,

        "button.fg": _WHITE,
        "button.bg": _ACCENT,
        "button.focused.fg": _WHITE,
        "button.focused.bg": _ACCENT_LIGHT,
        "button.pressed.fg": _WHITE,
        "button.pressed.bg": Color.from_rgb(0, 90, 160),

        "input.fg": _FG,
        "input.bg": _BG,
        "input.focused.fg": _WHITE,
        "input.focused.bg": Color.from_rgb(30, 30, 50),
        "input.cursor": _WHITE,
        "input.placeholder": _DIM,
        "input.selection.fg": _WHITE,
        "input.selection.bg": _ACCENT,

        "menu.bg": _SURFACE,
        "menu.fg": _FG,
        "menu.selected.bg": _ACCENT,
        "menu.selected.fg": _WHITE,
        "menu.hotkey": _ACCENT_LIGHT,
        "menu.disabled": _DIM,

        "checkbox.fg": _FG,
        "checkbox.bg": _SURFACE,
        "checkbox.focused.fg": _WHITE,
        "checkbox.focused.bg": _ACCENT,

        "scrollbar.track": _SURFACE_LIGHT,
        "scrollbar.thumb": _DIM,
        "scrollbar.arrow": _FG,

        "dialog.bg": _SURFACE,
        "dialog.fg": _FG,
        "dialog.border": _ACCENT,
        "dialog.title": _WHITE,

        "listbox.fg": _FG,
        "listbox.bg": _BG,
        "listbox.selected.fg": _WHITE,
        "listbox.selected.bg": _ACCENT,

        "dropdown.fg": _FG,
        "dropdown.bg": _SURFACE,
        "dropdown.arrow": _FG,

        "calendar.fg": _FG,
        "calendar.bg": _SURFACE,
        "calendar.today": _YELLOW,
        "calendar.selected": _ACCENT,
        "calendar.header": _WHITE,

        "taskbar.bg": Color.from_rgb(25, 25, 25),
        "taskbar.fg": _FG,
        "taskbar.active.bg": _ACCENT,
        "taskbar.active.fg": _WHITE,
    },
    borders={
        "window": BorderStyle.ROUNDED,
        "dialog": BorderStyle.ROUNDED,
        "container": BorderStyle.ROUNDED,
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

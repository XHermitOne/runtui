"""Modern light theme."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

_BG = Color.from_rgb(255, 255, 255)
_FG = Color.from_rgb(30, 30, 30)
_ACCENT = Color.from_rgb(0, 120, 212)
_ACCENT_LIGHT = Color.from_rgb(50, 150, 230)
_BORDER = Color.from_rgb(200, 200, 200)
_SURFACE = Color.from_rgb(245, 245, 245)
_WHITE = Color.from_rgb(255, 255, 255)
_BLACK = Color.from_rgb(0, 0, 0)
_RED = Color.from_rgb(200, 50, 50)
_GREEN = Color.from_rgb(50, 150, 50)
_YELLOW = Color.from_rgb(200, 150, 0)
_DIM = Color.from_rgb(160, 160, 160)
_SHADOW = Color.from_rgb(180, 180, 180)

light_theme = ThemeDefinition(
    name="light",
    colors={
        "desktop.bg": Color.from_rgb(230, 230, 230),
        "desktop.fg": Color.from_rgb(210, 210, 210),

        "window.bg": _BG,
        "window.fg": _FG,
        "window.border": _BORDER,
        "window.title": _FG,
        "window.title.bg": _BG,
        "window.active.border": _ACCENT,
        "window.active.title": _WHITE,
        "window.active.title.bg": _ACCENT,
        "window.button": _FG,
        "window.shadow": _SHADOW,

        "container.bg": _BG,
        "container.fg": _FG,
        "container.border": _BORDER,
        "container.title": _FG,

        "label.fg": _FG,
        "label.bg": _BG,

        "button.fg": _WHITE,
        "button.bg": _ACCENT,
        "button.focused.fg": _WHITE,
        "button.focused.bg": _ACCENT_LIGHT,
        "button.pressed.fg": _WHITE,
        "button.pressed.bg": Color.from_rgb(0, 90, 170),

        "input.fg": _FG,
        "input.bg": _BG,
        "input.focused.fg": _FG,
        "input.focused.bg": Color.from_rgb(255, 255, 230),
        "input.cursor": _FG,
        "input.placeholder": _DIM,
        "input.selection.fg": _WHITE,
        "input.selection.bg": _ACCENT,

        "menu.bg": _SURFACE,
        "menu.fg": _FG,
        "menu.selected.bg": _ACCENT,
        "menu.selected.fg": _WHITE,
        "menu.hotkey": _RED,
        "menu.disabled": _DIM,

        "checkbox.fg": _FG,
        "checkbox.bg": _BG,
        "checkbox.focused.fg": _WHITE,
        "checkbox.focused.bg": _ACCENT,

        "scrollbar.track": Color.from_rgb(230, 230, 230),
        "scrollbar.thumb": Color.from_rgb(160, 160, 160),
        "scrollbar.arrow": _FG,

        "dialog.bg": _SURFACE,
        "dialog.fg": _FG,
        "dialog.border": _ACCENT,
        "dialog.title": _FG,

        "listbox.fg": _FG,
        "listbox.bg": _BG,
        "listbox.selected.fg": _WHITE,
        "listbox.selected.bg": _ACCENT,

        "dropdown.fg": _FG,
        "dropdown.bg": _BG,
        "dropdown.arrow": _FG,

        "calendar.fg": _FG,
        "calendar.bg": _BG,
        "calendar.today": _YELLOW,
        "calendar.selected": _ACCENT,
        "calendar.header": _ACCENT,

        "taskbar.bg": _SURFACE,
        "taskbar.fg": _FG,
        "taskbar.active.bg": _ACCENT,
        "taskbar.active.fg": _WHITE,
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

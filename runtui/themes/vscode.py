"""VS Code Dark theme."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

# VS Code Palette
_BG_DARK = Color.from_hex("#1e1e1e")
_BG_SIDEBAR = Color.from_hex("#252526")
_BG_ACTIVBAR = Color.from_hex("#333333")
_FG_TEXT = Color.from_hex("#cccccc")
_FG_COMMENT = Color.from_hex("#6a9955")
_BLUE_ACCENT = Color.from_hex("#007acc")
_BLUE_DARK = Color.from_hex("#0e639c")
_BORDER = Color.from_hex("#454545")
_WIDGET_BG = Color.from_hex("#2d2d30")
_SELECTION = Color.from_hex("#264f78")
_ORANGE = Color.from_hex("#ce9178")
_YELLOW = Color.from_hex("#dcdcaa")
_WHITE = Color.from_hex("#ffffff")

vscode_theme = ThemeDefinition(
    name="vscode",
    colors={
        "desktop.bg": _BG_DARK,
        "desktop.fg": _FG_TEXT,

        "window.bg": _BG_SIDEBAR,
        "window.fg": _FG_TEXT,
        "window.border": _BORDER,
        "window.title": _FG_TEXT,
        "window.title.bg": _BG_SIDEBAR,
        "window.active.border": _BLUE_ACCENT,
        "window.active.title": _WHITE,
        "window.active.title.bg": _BLUE_ACCENT,
        "window.button": _FG_TEXT,
        "window.shadow": Color.from_hex("#000000"),

        "container.bg": _BG_DARK,
        "container.fg": _FG_TEXT,
        "container.border": _BORDER,
        "container.title": _BLUE_ACCENT,

        "label.fg": _FG_TEXT,
        "label.bg": _BG_SIDEBAR,

        "button.fg": _WHITE,
        "button.bg": _BLUE_DARK,
        "button.focused.fg": _WHITE,
        "button.focused.bg": _BLUE_ACCENT,
        "button.pressed.fg": _WHITE,
        "button.pressed.bg": _BG_ACTIVBAR,

        "input.fg": _FG_TEXT,
        "input.bg": _WIDGET_BG,
        "input.focused.fg": _WHITE,
        "input.focused.bg": _BG_ACTIVBAR,
        "input.cursor": _WHITE,
        "input.placeholder": _FG_COMMENT,
        "input.selection.fg": _WHITE,
        "input.selection.bg": _SELECTION,

        "menu.bg": _WIDGET_BG,
        "menu.fg": _FG_TEXT,
        "menu.selected.bg": _BLUE_ACCENT,
        "menu.selected.fg": _WHITE,
        "menu.hotkey": _ORANGE,
        "menu.disabled": _BORDER,

        "checkbox.fg": _FG_TEXT,
        "checkbox.bg": _BG_SIDEBAR,
        "checkbox.focused.fg": _WHITE,
        "checkbox.focused.bg": _SELECTION,

        "scrollbar.track": _BG_DARK,
        "scrollbar.thumb": _BORDER,
        "scrollbar.arrow": _FG_TEXT,

        "dialog.bg": _WIDGET_BG,
        "dialog.fg": _FG_TEXT,
        "dialog.border": _BLUE_ACCENT,
        "dialog.title": _WHITE,

        "listbox.fg": _FG_TEXT,
        "listbox.bg": _BG_DARK,
        "listbox.selected.fg": _WHITE,
        "listbox.selected.bg": _SELECTION,

        "dropdown.fg": _FG_TEXT,
        "dropdown.bg": _WIDGET_BG,
        "dropdown.arrow": _FG_TEXT,

        "calendar.fg": _FG_TEXT,
        "calendar.bg": _BG_SIDEBAR,
        "calendar.today": _YELLOW,
        "calendar.selected": _BLUE_ACCENT,
        "calendar.header": _BG_ACTIVBAR,

        "taskbar.bg": _BLUE_ACCENT,
        "taskbar.fg": _WHITE,
        "taskbar.active.bg": _BG_ACTIVBAR,
        "taskbar.active.fg": _WHITE,
    },
    borders={
        "window": BorderStyle.SINGLE,
        "dialog": BorderStyle.SINGLE,
        "container": BorderStyle.SINGLE,
        "input": BorderStyle.SINGLE,
    },
    glyphs={
        "checkbox.checked": "[✓]",
        "checkbox.unchecked": "[ ]",
        "radio.selected": "(●)",
        "radio.unselected": "(○)",
        "scrollbar.thumb": " ",
        "scrollbar.track": "░",
        "scrollbar.up": "^",
        "scrollbar.down": "v",
        "scrollbar.left": "<",
        "scrollbar.right": ">",
        "window.close": "[x]",
        "window.maximize": "[□]",
        "window.minimize": "[—]",
        "window.restore": "[❐]",
        "menu.arrow": ">",
        "menu.separator": "─",
        "dropdown.arrow": "v",
        "cursor.arrow": "▶",
        "cursor.hand": "👆",
        "cursor.text": "│",
    },
)
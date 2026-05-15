"""GitHub Light theme."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

# GitHub Palette
_WHITE = Color.from_hex("#ffffff")
_BG_GRAY = Color.from_hex("#f6f8fa")
_BORDER_GRAY = Color.from_hex("#d0d7de")
_TEXT_MAIN = Color.from_hex("#24292f")
_TEXT_MUTED = Color.from_hex("#57606a")
_BLUE_ACCENT = Color.from_hex("#0969da")
_GREEN_BTN = Color.from_hex("#2da44e")
_RED_DANGER = Color.from_hex("#cf222e")
_YELLOW_ATTN = Color.from_hex("#9a6700")
_INPUT_BG = Color.from_hex("#f6f8fa")
_SELECTION = Color.from_hex("#ddf4ff")

NAME = "github"

github_theme = ThemeDefinition(
    name=NAME,
    colors={
        "desktop.bg": _BG_GRAY,
        "desktop.fg": _TEXT_MAIN,

        "window.bg": _WHITE,
        "window.fg": _TEXT_MAIN,
        "window.border": _BORDER_GRAY,
        "window.title": _TEXT_MAIN,
        "window.title.bg": _WHITE,
        "window.active.border": _BLUE_ACCENT,
        "window.active.title": _WHITE,
        "window.active.title.bg": _BLUE_ACCENT,
        "window.button": _TEXT_MUTED,
        "window.shadow": _TEXT_MUTED,

        "container.bg": _WHITE,
        "container.fg": _TEXT_MAIN,
        "container.border": _BORDER_GRAY,
        "container.title": _TEXT_MAIN,

        "label.fg": _TEXT_MAIN,
        "label.bg": _WHITE,

        "button.fg": _WHITE,
        "button.bg": _GREEN_BTN,
        "button.focused.fg": _WHITE,
        "button.focused.bg": _BLUE_ACCENT,
        "button.pressed.fg": _WHITE,
        "button.pressed.bg": _TEXT_MAIN,

        "input.fg": _TEXT_MAIN,
        "input.bg": _INPUT_BG,
        "input.focused.fg": _TEXT_MAIN,
        "input.focused.bg": _WHITE,
        "input.cursor": _BLUE_ACCENT,
        "input.placeholder": _TEXT_MUTED,
        "input.selection.fg": _BLUE_ACCENT,
        "input.selection.bg": _SELECTION,

        "menu.bg": _WHITE,
        "menu.fg": _TEXT_MAIN,
        "menu.selected.bg": _BLUE_ACCENT,
        "menu.selected.fg": _WHITE,
        "menu.hotkey": _RED_DANGER,
        "menu.disabled": _BORDER_GRAY,

        "checkbox.fg": _TEXT_MAIN,
        "checkbox.bg": _WHITE,
        "checkbox.focused.fg": _WHITE,
        "checkbox.focused.bg": _BLUE_ACCENT,

        "scrollbar.track": _BG_GRAY,
        "scrollbar.thumb": _BORDER_GRAY,
        "scrollbar.arrow": _TEXT_MUTED,

        "dialog.bg": _WHITE,
        "dialog.fg": _TEXT_MAIN,
        "dialog.border": _BORDER_GRAY,
        "dialog.title": _TEXT_MAIN,

        "listbox.fg": _TEXT_MAIN,
        "listbox.bg": _WHITE,
        "listbox.selected.fg": _WHITE,
        "listbox.selected.bg": _BLUE_ACCENT,

        "dropdown.fg": _TEXT_MAIN,
        "dropdown.bg": _INPUT_BG,
        "dropdown.arrow": _TEXT_MUTED,

        "calendar.fg": _TEXT_MAIN,
        "calendar.bg": _WHITE,
        "calendar.today": _GREEN_BTN,
        "calendar.selected": _BLUE_ACCENT,
        "calendar.header": _BG_GRAY,

        "taskbar.bg": _TEXT_MAIN,
        "taskbar.fg": _WHITE,
        "taskbar.active.bg": _BLUE_ACCENT,
        "taskbar.active.fg": _WHITE,
    },
    borders={
        "window": BorderStyle.SINGLE,
        "dialog": BorderStyle.DOUBLE,
        "container": BorderStyle.SINGLE,
        "input": BorderStyle.SINGLE,
    },
    glyphs={
        "checkbox.checked": "[x]",
        "checkbox.unchecked": "[ ]",
        "radio.selected": "(•)",
        "radio.unselected": "( )",
        "scrollbar.thumb": "│",
        "scrollbar.track": " ",
        "scrollbar.up": "▴",
        "scrollbar.down": "▾",
        "scrollbar.left": "◂",
        "scrollbar.right": "▸",
        # "window.close": "✕",
        # "window.maximize": "□",
        # "window.minimize": "─",
        # "window.restore": "❐",
        "window.close": "[×]",
        "window.maximize": "[▲]",
        "window.minimize": "[▼]",
        "window.restore": "[❐]",

        "menu.arrow": "→",
        "menu.separator": "─",
        "dropdown.arrow": "▼",
        "cursor.arrow": "➤",
        "cursor.hand": "👆",
        "cursor.text": "I",
    },
)
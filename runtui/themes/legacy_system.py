"""Legacy System (DOS/BIOS) theme."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

# BIOS/DOS Palette
_BIOS_BLUE = Color.from_hex("#0000aa")
_BIOS_GRAY = Color.from_hex("#aaaaaa")
_BIOS_WHITE = Color.from_hex("#ffffff")
_BIOS_RED = Color.from_hex("#aa0000")       # Only for hotkeys/warnings
_BIOS_YELLOW = Color.from_hex("#ffff55")
_BIOS_CYAN = Color.from_hex("#00aaaa")      # Used for selections
_BIOS_BLACK = Color.from_hex("#000000")

legacy_system_theme = ThemeDefinition(
    name="legacy_system",
    colors={
        "desktop.bg": _BIOS_BLUE,
        "desktop.fg": _BIOS_GRAY,

        "window.bg": _BIOS_GRAY,
        "window.fg": _BIOS_BLUE,
        "window.border": _BIOS_BLUE,
        "window.title": _BIOS_BLUE,
        "window.title.bg": _BIOS_GRAY,
        
        # Changed Active Title to Cyan bg / Black fg (Classic BIOS active state)
        "window.active.border": _BIOS_WHITE,
        "window.active.title": _BIOS_BLACK,
        "window.active.title.bg": _BIOS_CYAN,
        
        "window.button": _BIOS_BLACK,
        "window.shadow": _BIOS_BLACK,

        "container.bg": _BIOS_GRAY,
        "container.fg": _BIOS_BLUE,
        "container.border": _BIOS_BLUE,
        "container.title": _BIOS_BLACK,

        "label.fg": _BIOS_BLUE,
        "label.bg": _BIOS_GRAY,

        # Buttons: Gray standard, Cyan focused
        "button.fg": _BIOS_BLACK,
        "button.bg": _BIOS_WHITE,
        "button.focused.fg": _BIOS_BLACK,
        "button.focused.bg": _BIOS_CYAN,
        "button.pressed.fg": _BIOS_YELLOW,
        "button.pressed.bg": _BIOS_BLUE,

        "input.fg": _BIOS_WHITE,
        "input.bg": _BIOS_BLUE,
        "input.focused.fg": _BIOS_YELLOW,
        "input.focused.bg": _BIOS_BLUE,
        "input.cursor": _BIOS_YELLOW,
        "input.placeholder": _BIOS_CYAN,
        "input.selection.fg": _BIOS_WHITE,
        "input.selection.bg": _BIOS_CYAN,

        "menu.bg": _BIOS_GRAY,
        "menu.fg": _BIOS_BLACK,
        "menu.selected.bg": _BIOS_CYAN, # Changed from Red to Cyan
        "menu.selected.fg": _BIOS_BLACK,
        "menu.hotkey": _BIOS_RED,       # Keep red for hotkeys
        "menu.disabled": _BIOS_WHITE,

        "checkbox.fg": _BIOS_BLUE,
        "checkbox.bg": _BIOS_GRAY,
        "checkbox.focused.fg": _BIOS_BLACK,
        "checkbox.focused.bg": _BIOS_CYAN,

        "scrollbar.track": _BIOS_GRAY,
        "scrollbar.thumb": _BIOS_BLUE,
        "scrollbar.arrow": _BIOS_BLACK,

        # Dialogs: Gray background (Turbo Vision style) instead of Red
        "dialog.bg": _BIOS_GRAY,
        "dialog.fg": _BIOS_BLACK,
        "dialog.border": _BIOS_BLUE,
        "dialog.title": _BIOS_BLUE,

        "listbox.fg": _BIOS_WHITE,
        "listbox.bg": _BIOS_BLUE,
        "listbox.selected.fg": _BIOS_BLACK,
        "listbox.selected.bg": _BIOS_CYAN,

        "dropdown.fg": _BIOS_WHITE,
        "dropdown.bg": _BIOS_BLUE,
        "dropdown.arrow": _BIOS_YELLOW,

        "calendar.fg": _BIOS_BLUE,
        "calendar.bg": _BIOS_GRAY,
        "calendar.today": _BIOS_CYAN,
        "calendar.selected": _BIOS_WHITE,
        "calendar.header": _BIOS_BLUE,

        # Taskbar: Cyan active state
        "taskbar.bg": _BIOS_GRAY,
        "taskbar.fg": _BIOS_BLUE,
        "taskbar.active.bg": _BIOS_CYAN,
        "taskbar.active.fg": _BIOS_BLACK,
    },
    borders={
        "window": BorderStyle.DOUBLE,
        "dialog": BorderStyle.DOUBLE,
        "container": BorderStyle.SINGLE,
        "input": BorderStyle.SINGLE,
    },
    glyphs={
        "checkbox.checked": "[■]",
        "checkbox.unchecked": "[ ]",
        "radio.selected": "(■)",
        "radio.unselected": "( )",
        "scrollbar.thumb": "░",
        "scrollbar.track": "│",
        "scrollbar.up": "▲",
        "scrollbar.down": "▼",
        "scrollbar.left": "◄",
        "scrollbar.right": "►",
        "window.close": "[x]",
        "window.maximize": "[^]",
        "window.minimize": "[_]",
        "window.restore": "[=]",
        "menu.arrow": "►",
        "menu.separator": "─",
        "dropdown.arrow": "▼",
        "cursor.arrow": "►",
        "cursor.hand": "»",
        "cursor.text": "│",
    },
)
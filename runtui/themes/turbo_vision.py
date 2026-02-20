"""Turbo Vision theme -- classic Borland DOS-era look."""

from ..core.types import BorderStyle, Color
from .engine import ThemeDefinition

# Turbo Vision classic palette (ANSI terminal indexed colors)
# Mapping from DOS CGA to ANSI:
#   DOS 1 (blue) -> ANSI 4, DOS 3 (cyan) -> ANSI 6, DOS 7 (light gray) -> ANSI 7
_TV_BLUE = Color.from_index(4)       # Blue (desktop bg)
_TV_CYAN = Color.from_index(6)       # Cyan (selection highlight, focused inputs)
_TV_WHITE = Color.from_index(15)     # Bright white (active borders, titles)
_TV_BLACK = Color.from_index(0)      # Black (text)
_TV_YELLOW = Color.from_index(11)    # Bright yellow (calendar today)
_TV_GREEN = Color.from_index(2)      # Green (menu bar, buttons)
_TV_RED = Color.from_index(1)        # Red (hotkeys)
_TV_GRAY = Color.from_index(7)       # Light gray (window/dialog bg)
_TV_DARK_GRAY = Color.from_index(8)  # Dark gray (shadows, disabled)
_TV_LIGHT_BLUE = Color.from_index(12)  # Bright blue (desktop pattern)
_TV_BRIGHT_CYAN = Color.from_index(14) # Bright cyan

turbo_vision_theme = ThemeDefinition(
    name="turbo_vision",
    colors={
        # Desktop
        "desktop.bg": _TV_BLUE,
        "desktop.fg": _TV_LIGHT_BLUE,

        # Window (light gray background like classic TV)
        "window.bg": _TV_GRAY,
        "window.fg": _TV_BLACK,
        "window.border": _TV_GRAY,
        #"window.title": _TV_BLACK,
        "window.title": _TV_WHITE,
        "window.title.bg": _TV_GRAY,
        "window.active.bg": _TV_GRAY,
        "window.active.fg": _TV_BLACK,
        "window.active.border": _TV_WHITE,
        #"window.active.title": _TV_WHITE,
        "window.active.title": _TV_BLACK,
        #"window.active.title.bg": _TV_CYAN,
        "window.active.title.bg": _TV_GRAY,
        "window.button": _TV_BLACK,
        "window.shadow": _TV_DARK_GRAY,

        # Container
        "container.bg": _TV_GRAY,
        "container.fg": _TV_BLACK,
        "container.border": _TV_BLACK,
        "container.title": _TV_BLACK,

        # Label
        "label.fg": _TV_BLACK,
        "label.bg": _TV_GRAY,

        # Button (green with black text, like classic TV)
        "button.fg": _TV_WHITE,
        "button.bg": _TV_GREEN,
        "button.focused.fg": _TV_WHITE,
        "button.focused.bg": _TV_CYAN,
        "button.pressed.fg": _TV_WHITE,
        "button.pressed.bg": _TV_GREEN,
        "button.shadow": _TV_DARK_GRAY,

        # Input (cyan bg for input fields when focused)
        "input.fg": _TV_BLUE,
        "input.bg": _TV_CYAN,
        "input.focused.fg": _TV_YELLOW,
        "input.focused.bg": _TV_BLUE,
        "input.cursor": _TV_WHITE,
        "input.selection.fg": _TV_BLACK,
        "input.selection.bg": _TV_CYAN,

        # Menu (green bg like classic TV menu bar)
        # "menu.bg": _TV_GREEN,
        # "menu.fg": _TV_BLACK,
        # "menu.selected.bg": _TV_CYAN,
        # "menu.selected.fg": _TV_WHITE,

        "menu.bg": _TV_GRAY,
        "menu.fg": _TV_BLACK,
        "menu.selected.bg": _TV_GREEN,
        "menu.selected.fg": _TV_BLACK,

        "menu.hotkey": _TV_RED,
        "menu.disabled": _TV_DARK_GRAY,

        # Checkbox / Radio
        "checkbox.fg": _TV_BLACK,
        "checkbox.bg": _TV_GRAY,
        "checkbox.focused.fg": _TV_YELLOW,
        "checkbox.focused.bg": _TV_BLUE,

        # Scrollbar
        "scrollbar.track": _TV_GRAY,
        "scrollbar.thumb": _TV_BLACK,
        "scrollbar.arrow": _TV_BLACK,

        # Dialog (gray bg with white border like classic TV)
        "dialog.bg": _TV_GRAY,
        "dialog.fg": _TV_BLACK,
        "dialog.border": _TV_WHITE,
        "dialog.title": _TV_WHITE,

        # Listbox
        "listbox.fg": _TV_BLACK,
        "listbox.bg": _TV_CYAN,
        "listbox.selected.fg": _TV_WHITE,
        "listbox.selected.bg": _TV_GREEN,

        # Dropdown
        "dropdown.fg": _TV_BLACK,
        "dropdown.bg": _TV_GRAY,
        "dropdown.arrow": _TV_BLACK,

        # Calendar
        "calendar.fg": _TV_BLACK,
        "calendar.bg": _TV_CYAN,
        "calendar.today": _TV_YELLOW,
        "calendar.selected": _TV_GREEN,
        "calendar.header": _TV_WHITE,

        # Progress bar
        "progressbar.fg": _TV_CYAN,
        "progressbar.bg": _TV_GRAY,

        # Taskbar (cyan bg like classic TV status line)
        "taskbar.bg": _TV_CYAN,
        "taskbar.fg": _TV_BLACK,
        "taskbar.active.bg": _TV_GREEN,
        "taskbar.active.fg": _TV_WHITE,
    },
    borders={
        "window": BorderStyle.DOUBLE,
        "dialog": BorderStyle.DOUBLE,
        "container": BorderStyle.SINGLE,
        "input": BorderStyle.SINGLE,
    },
    glyphs={
        "checkbox.checked": "[X]",
        "checkbox.unchecked": "[ ]",
        "radio.selected": "(*)",
        "radio.unselected": "( )",
        "scrollbar.thumb": "█",
        "scrollbar.track": "░",
        "scrollbar.up": "▲",
        "scrollbar.down": "▼",
        "scrollbar.left": "◄",
        "scrollbar.right": "►",
        "window.close": "[■]",
        "window.maximize": "[▲]",
        "window.minimize": "[▼]",
        "window.restore": "[◊]",
        "menu.arrow": "►",
        "menu.separator": "─",
        "dropdown.arrow": "▼",
        "cursor.arrow": "▶",
        "cursor.hand": "☞",
        "cursor.text": "│",
    },
)

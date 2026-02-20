"""Key constants and modifier flags."""

from __future__ import annotations

import enum


class Modifiers(enum.Flag):
    NONE = 0
    SHIFT = enum.auto()
    ALT = enum.auto()
    CTRL = enum.auto()
    META = enum.auto()


class Keys(enum.Enum):
    """Named key constants."""
    # Special
    UNKNOWN = "unknown"
    ESCAPE = "escape"
    ENTER = "enter"
    TAB = "tab"
    BACKSPACE = "backspace"
    DELETE = "delete"
    INSERT = "insert"
    SPACE = "space"

    # Navigation
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    HOME = "home"
    END = "end"
    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"

    # Function keys
    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F4 = "f4"
    F5 = "f5"
    F6 = "f6"
    F7 = "f7"
    F8 = "f8"
    F9 = "f9"
    F10 = "f10"
    F11 = "f11"
    F12 = "f12"

    # Character (placeholder, actual char is in KeyEvent.char)
    CHAR = "char"


class MouseButton(enum.Enum):
    NONE = 0
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3
    SCROLL_UP = 4
    SCROLL_DOWN = 5


class MouseAction(enum.Enum):
    PRESS = "press"
    RELEASE = "release"
    MOVE = "move"
    DRAG = "drag"


# Mapping for CSI sequences to Keys
_CSI_KEY_MAP: dict[str, Keys] = {
    "A": Keys.UP,
    "B": Keys.DOWN,
    "C": Keys.RIGHT,
    "D": Keys.LEFT,
    "H": Keys.HOME,
    "F": Keys.END,
    "Z": Keys.TAB,  # Shift+Tab
}

_CSI_TILDE_MAP: dict[int, Keys] = {
    1: Keys.HOME,
    2: Keys.INSERT,
    3: Keys.DELETE,
    4: Keys.END,
    5: Keys.PAGE_UP,
    6: Keys.PAGE_DOWN,
    11: Keys.F1,
    12: Keys.F2,
    13: Keys.F3,
    14: Keys.F4,
    15: Keys.F5,
    17: Keys.F6,
    18: Keys.F7,
    19: Keys.F8,
    20: Keys.F9,
    21: Keys.F10,
    23: Keys.F11,
    24: Keys.F12,
}

# SS3 function key mapping
_SS3_KEY_MAP: dict[str, Keys] = {
    "P": Keys.F1,
    "Q": Keys.F2,
    "R": Keys.F3,
    "S": Keys.F4,
    "H": Keys.HOME,
    "F": Keys.END,
}


def decode_modifiers_from_param(param: int) -> Modifiers:
    """Decode xterm modifier parameter (param - 1 is the bitmask)."""
    mod = Modifiers.NONE
    bits = param - 1
    if bits & 1:
        mod |= Modifiers.SHIFT
    if bits & 2:
        mod |= Modifiers.ALT
    if bits & 4:
        mod |= Modifiers.CTRL
    if bits & 8:
        mod |= Modifiers.META
    return mod

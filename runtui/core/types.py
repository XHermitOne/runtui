"""Fundamental types: Point, Size, Rect, Color, Attrs, Cell."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class Point:
    x: int = 0
    y: int = 0

    def offset(self, dx: int, dy: int) -> Point:
        return Point(self.x + dx, self.y + dy)

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y)


@dataclass(slots=True, frozen=True)
class Size:
    width: int = 0
    height: int = 0

    @property
    def area(self) -> int:
        return self.width * self.height

    def constrain(self, min_size: Size | None = None, max_size: Size | None = None) -> Size:
        w, h = self.width, self.height
        if min_size:
            w = max(w, min_size.width)
            h = max(h, min_size.height)
        if max_size:
            w = min(w, max_size.width)
            h = min(h, max_size.height)
        return Size(w, h)


@dataclass(slots=True, frozen=True)
class Rect:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def origin(self) -> Point:
        return Point(self.x, self.y)

    @property
    def size(self) -> Size:
        return Size(self.width, self.height)

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.right and self.y <= y < self.bottom

    def intersect(self, other: Rect) -> Rect:
        x1 = max(self.x, other.x)
        y1 = max(self.y, other.y)
        x2 = min(self.right, other.right)
        y2 = min(self.bottom, other.bottom)
        if x2 <= x1 or y2 <= y1:
            return Rect(0, 0, 0, 0)
        return Rect(x1, y1, x2 - x1, y2 - y1)

    def union(self, other: Rect) -> Rect:
        if self.width == 0 or self.height == 0:
            return other
        if other.width == 0 or other.height == 0:
            return self
        x1 = min(self.x, other.x)
        y1 = min(self.y, other.y)
        x2 = max(self.right, other.right)
        y2 = max(self.bottom, other.bottom)
        return Rect(x1, y1, x2 - x1, y2 - y1)

    def offset(self, dx: int, dy: int) -> Rect:
        return Rect(self.x + dx, self.y + dy, self.width, self.height)

    def inset(self, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0) -> Rect:
        return Rect(
            self.x + left,
            self.y + top,
            max(0, self.width - left - right),
            max(0, self.height - top - bottom),
        )

    @staticmethod
    def from_points(p1: Point, p2: Point) -> Rect:
        x1, x2 = min(p1.x, p2.x), max(p1.x, p2.x)
        y1, y2 = min(p1.y, p2.y), max(p1.y, p2.y)
        return Rect(x1, y1, x2 - x1, y2 - y1)


class ColorMode(enum.Enum):
    DEFAULT = "default"
    INDEXED = "indexed"
    RGB = "rgb"


@dataclass(frozen=True)
class Color:
    r: int = 0
    g: int = 0
    b: int = 0
    mode: ColorMode = ColorMode.RGB
    index: int = -1  # For indexed colors (0-255)

    @staticmethod
    def from_rgb(r: int, g: int, b: int) -> Color:
        return Color(r, g, b, ColorMode.RGB)

    @staticmethod
    def from_index(index: int) -> Color:
        return Color(0, 0, 0, ColorMode.INDEXED, index)

    @staticmethod
    def from_default() -> Color:
        return Color(0, 0, 0, ColorMode.DEFAULT)

    @staticmethod
    def from_hex(hex_str: str) -> Color:
        hex_str = hex_str.lstrip("#")
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return Color.from_rgb(r, g, b)

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def fg_sequence(self) -> str:
        if self.mode == ColorMode.DEFAULT:
            return "\x1b[39m"
        elif self.mode == ColorMode.INDEXED:
            if self.index < 8:
                return f"\x1b[{30 + self.index}m"
            elif self.index < 16:
                return f"\x1b[{90 + self.index - 8}m"
            else:
                return f"\x1b[38;5;{self.index}m"
        else:
            return f"\x1b[38;2;{self.r};{self.g};{self.b}m"

    def bg_sequence(self) -> str:
        if self.mode == ColorMode.DEFAULT:
            return "\x1b[49m"
        elif self.mode == ColorMode.INDEXED:
            if self.index < 8:
                return f"\x1b[{40 + self.index}m"
            elif self.index < 16:
                return f"\x1b[{100 + self.index - 8}m"
            else:
                return f"\x1b[48;5;{self.index}m"
        else:
            return f"\x1b[48;2;{self.r};{self.g};{self.b}m"


# Standard colors using indexed mode for maximum compatibility
Color.DEFAULT = Color.from_default()
Color.BLACK = Color.from_index(0)
Color.RED = Color.from_index(1)
Color.GREEN = Color.from_index(2)
Color.YELLOW = Color.from_index(3)
Color.BLUE = Color.from_index(4)
Color.MAGENTA = Color.from_index(5)
Color.CYAN = Color.from_index(6)
Color.WHITE = Color.from_index(7)
Color.BRIGHT_BLACK = Color.from_index(8)
Color.BRIGHT_RED = Color.from_index(9)
Color.BRIGHT_GREEN = Color.from_index(10)
Color.BRIGHT_YELLOW = Color.from_index(11)
Color.BRIGHT_BLUE = Color.from_index(12)
Color.BRIGHT_MAGENTA = Color.from_index(13)
Color.BRIGHT_CYAN = Color.from_index(14)
Color.BRIGHT_WHITE = Color.from_index(15)


class Attrs(enum.Flag):
    NONE = 0
    BOLD = enum.auto()
    DIM = enum.auto()
    ITALIC = enum.auto()
    UNDERLINE = enum.auto()
    BLINK = enum.auto()
    REVERSE = enum.auto()
    STRIKETHROUGH = enum.auto()


def attrs_sequence(attrs: Attrs) -> str:
    codes: list[str] = []
    if Attrs.BOLD in attrs:
        codes.append("1")
    if Attrs.DIM in attrs:
        codes.append("2")
    if Attrs.ITALIC in attrs:
        codes.append("3")
    if Attrs.UNDERLINE in attrs:
        codes.append("4")
    if Attrs.BLINK in attrs:
        codes.append("5")
    if Attrs.REVERSE in attrs:
        codes.append("7")
    if Attrs.STRIKETHROUGH in attrs:
        codes.append("9")
    if codes:
        return "\x1b[" + ";".join(codes) + "m"
    return ""


@dataclass(slots=True)
class Cell:
    char: str = " "
    fg: Color = field(default_factory=Color.from_default)
    bg: Color = field(default_factory=Color.from_default)
    attrs: Attrs = Attrs.NONE
    wide: bool = False  # True if continuation of a wide char

    def copy_from(self, other: Cell) -> None:
        self.char = other.char
        self.fg = other.fg
        self.bg = other.bg
        self.attrs = other.attrs
        self.wide = other.wide

    def equals(self, other: Cell) -> bool:
        return (
            self.char == other.char
            and self.fg == other.fg
            and self.bg == other.bg
            and self.attrs == other.attrs
            and self.wide == other.wide
        )

    def reset(self) -> None:
        self.char = " "
        self.fg = Color.DEFAULT
        self.bg = Color.DEFAULT
        self.attrs = Attrs.NONE
        self.wide = False


class ColorDepth(enum.Enum):
    MONO = 1
    COLORS_16 = 16
    COLORS_256 = 256
    TRUE_COLOR = 16777216


class BorderStyle(enum.Enum):
    NONE = "none"
    SINGLE = "single"
    DOUBLE = "double"
    HEAVY = "heavy"
    ROUNDED = "rounded"
    ASCII = "ascii"


@dataclass(slots=True, frozen=True)
class BorderChars:
    top_left: str
    top: str
    top_right: str
    left: str
    right: str
    bottom_left: str
    bottom: str
    bottom_right: str

    @staticmethod
    def for_style(style: BorderStyle) -> BorderChars:
        return _BORDER_CHARS.get(style, _BORDER_CHARS[BorderStyle.SINGLE])


_BORDER_CHARS: dict[BorderStyle, BorderChars] = {
    BorderStyle.NONE: BorderChars(" ", " ", " ", " ", " ", " ", " ", " "),
    BorderStyle.SINGLE: BorderChars("┌", "─", "┐", "│", "│", "└", "─", "┘"),
    BorderStyle.DOUBLE: BorderChars("╔", "═", "╗", "║", "║", "╚", "═", "╝"),
    BorderStyle.HEAVY: BorderChars("┏", "━", "┓", "┃", "┃", "┗", "━", "┛"),
    BorderStyle.ROUNDED: BorderChars("╭", "─", "╮", "│", "│", "╰", "─", "╯"),
    BorderStyle.ASCII: BorderChars("+", "-", "+", "|", "|", "+", "-", "+"),
}

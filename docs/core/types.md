# types.py - Fundamental Types

Core data types used throughout the runtui framework.

---

## Class: `Point`

A 2D point with x and y coordinates.

### Constructor

```python
@dataclass(slots=True, frozen=True)
class Point:
    x: int = 0
    y: int = 0
```

### Methods

#### `offset`
```python
def offset(self, dx: int, dy: int) -> Point
```
Returns a new point offset by the given delta values.

**Parameters:**
- `dx` (`int`): Horizontal offset
- `dy` (`int`): Vertical offset

**Returns:** `Point` - A new offset point

#### `__add__`
```python
def __add__(self, other: Point) -> Point
```
Add two points together.

#### `__sub__`
```python
def __sub__(self, other: Point) -> Point
```
Subtract another point from this one.

---

## Class: `Size`

Width and height dimensions.

### Constructor

```python
@dataclass(slots=True, frozen=True)
class Size:
    width: int = 0
    height: int = 0
```

### Properties

#### `area`
```python
@property
def area(self) -> int
```
Returns the area (width * height).

### Methods

#### `constrain`
```python
def constrain(
    self,
    min_size: Size | None = None,
    max_size: Size | None = None,
) -> Size
```
Constrain the size to minimum and maximum bounds.

**Parameters:**
- `min_size` (`Size | None`): Minimum size constraint
- `max_size` (`Size | None`): Maximum size constraint

**Returns:** `Size` - The constrained size

---

## Class: `Rect`

A rectangle with position (x, y) and dimensions (width, height).

### Constructor

```python
@dataclass(slots=True, frozen=True)
class Rect:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `left` | `int` | Same as `x` |
| `top` | `int` | Same as `y` |
| `right` | `int` | `x + width` |
| `bottom` | `int` | `y + height` |
| `origin` | `Point` | Top-left corner as a Point |
| `size` | `Size` | Width and height as a Size |

### Methods

#### `contains`
```python
def contains(self, x: int, y: int) -> bool
```
Check if a point is inside the rectangle.

**Parameters:**
- `x` (`int`): X coordinate
- `y` (`int`): Y coordinate

**Returns:** `bool` - True if the point is inside

#### `intersect`
```python
def intersect(self, other: Rect) -> Rect
```
Return the intersection of two rectangles.

**Parameters:**
- `other` (`Rect`): Another rectangle

**Returns:** `Rect` - The intersection rectangle (empty if no overlap)

#### `union`
```python
def union(self, other: Rect) -> Rect
```
Return the union of two rectangles.

**Parameters:**
- `other` (`Rect`): Another rectangle

**Returns:** `Rect` - The bounding rectangle

#### `offset`
```python
def offset(self, dx: int, dy: int) -> Rect
```
Return a new rectangle offset by the given deltas.

**Parameters:**
- `dx` (`int`): Horizontal offset
- `dy` (`int`): Vertical offset

**Returns:** `Rect` - The offset rectangle

#### `inset`
```python
def inset(
    self,
    top: int = 0,
    right: int = 0,
    bottom: int = 0,
    left: int = 0,
) -> Rect
```
Return a rectangle shrunk by the given insets.

**Returns:** `Rect` - The inset rectangle

#### `from_points`
```python
@staticmethod
def from_points(p1: Point, p2: Point) -> Rect
```
Create a rectangle from two corner points.

**Parameters:**
- `p1` (`Point`): First corner
- `p2` (`Point`): Second corner

**Returns:** `Rect` - The bounding rectangle

---

## Class: `Color`

Represents a terminal color (default, indexed, or RGB).

### Constructor

```python
@dataclass(frozen=True)
class Color:
    r: int = 0
    g: int = 0
    b: int = 0
    mode: ColorMode = ColorMode.RGB
    index: int = -1  # For indexed colors (0-255)
```

### Static Factory Methods

#### `from_rgb`
```python
@staticmethod
def from_rgb(r: int, g: int, b: int) -> Color
```
Create an RGB color (0-255 per channel).

**Parameters:**
- `r` (`int`): Red component
- `g` (`int`): Green component
- `b` (`int`): Blue component

**Returns:** `Color` - A new RGB color

#### `from_index`
```python
@staticmethod
def from_index(index: int) -> Color
```
Create an indexed color (0-255 terminal palette).

**Parameters:**
- `index` (`int`): Palette index (0-255)

**Returns:** `Color` - A new indexed color

#### `from_default`
```python
@staticmethod
def from_default() -> Color
```
Create a default color (uses terminal's default).

**Returns:** `Color` - The default color

#### `from_hex`
```python
@staticmethod
def from_hex(hex_str: str) -> Color
```
Create a color from a hex string like `"#RRGGBB"`.

**Parameters:**
- `hex_str` (`str`): Hex color string

**Returns:** `Color` - A new RGB color

### Methods

#### `to_hex`
```python
def to_hex(self) -> str
```
Convert the color to a hex string.

**Returns:** `str` - Hex color string like `"#rrggbb"`

#### `fg_sequence`
```python
def fg_sequence(self) -> str
```
Get the ANSI escape sequence for foreground color.

**Returns:** `str` - ANSI escape sequence

#### `bg_sequence`
```python
def bg_sequence(self) -> str
```
Get the ANSI escape sequence for background color.

**Returns:** `str` - ANSI escape sequence

### Predefined Colors

| Constant | Index | Description |
|----------|-------|-------------|
| `Color.DEFAULT` | - | Terminal default |
| `Color.BLACK` | 0 | Black |
| `Color.RED` | 1 | Red |
| `Color.GREEN` | 2 | Green |
| `Color.YELLOW` | 3 | Yellow |
| `Color.BLUE` | 4 | Blue |
| `Color.MAGENTA` | 5 | Magenta |
| `Color.CYAN` | 6 | Cyan |
| `Color.WHITE` | 7 | White |
| `Color.BRIGHT_BLACK` | 8 | Bright black (gray) |
| `Color.BRIGHT_RED` | 9 | Bright red |
| `Color.BRIGHT_GREEN` | 10 | Bright green |
| `Color.BRIGHT_YELLOW` | 11 | Bright yellow |
| `Color.BRIGHT_BLUE` | 12 | Bright blue |
| `Color.BRIGHT_MAGENTA` | 13 | Bright magenta |
| `Color.BRIGHT_CYAN` | 14 | Bright cyan |
| `Color.BRIGHT_WHITE` | 15 | Bright white |

---

## Enum: `ColorMode`

Color representation mode.

| Value | Description |
|-------|-------------|
| `DEFAULT` | Use terminal default color |
| `INDEXED` | Use 0-255 terminal palette |
| `RGB` | Use true-color RGB |

---

## Enum: `Attrs`

Text attribute flags that can be combined.

| Flag | ANSI Code | Description |
|------|-----------|-------------|
| `NONE` | - | No attributes |
| `BOLD` | 1 | Bold text |
| `DIM` | 2 | Dim/faint text |
| `ITALIC` | 3 | Italic text |
| `UNDERLINE` | 4 | Underlined text |
| `BLINK` | 5 | Blinking text |
| `REVERSE` | 7 | Reverse video |
| `STRIKETHROUGH` | 9 | Strikethrough |

### Function: `attrs_sequence`

```python
def attrs_sequence(attrs: Attrs) -> str
```
Convert attributes to an ANSI escape sequence.

**Parameters:**
- `attrs` (`Attrs`): Attribute flags

**Returns:** `str` - ANSI escape sequence

---

## Class: `Cell`

A single cell in the terminal buffer.

### Constructor

```python
@dataclass(slots=True)
class Cell:
    char: str = " "
    fg: Color = field(default_factory=Color.from_default)
    bg: Color = field(default_factory=Color.from_default)
    attrs: Attrs = Attrs.NONE
    wide: bool = False  # True if continuation of a wide char
```

### Methods

#### `copy_from`
```python
def copy_from(self, other: Cell) -> None
```
Copy all attributes from another cell.

**Parameters:**
- `other` (`Cell`): Source cell

#### `equals`
```python
def equals(self, other: Cell) -> bool
```
Check if this cell equals another.

**Parameters:**
- `other` (`Cell`): Cell to compare

**Returns:** `bool` - True if equal

#### `reset`
```python
def reset(self) -> None
```
Reset the cell to default state (space with default colors).

---

## Enum: `ColorDepth`

Terminal color depth capability.

| Value | Description |
|-------|-------------|
| `MONO` | Monochrome (no colors) |
| `COLORS_16` | 16-color mode |
| `COLORS_256` | 256-color mode |
| `TRUE_COLOR` | 24-bit true color |

---

## Enum: `BorderStyle`

Border rendering style.

| Value | Description |
|-------|-------------|
| `NONE` | No border |
| `SINGLE` | Single-line Unicode box |
| `DOUBLE` | Double-line Unicode box |
| `HEAVY` | Heavy/thick Unicode box |
| `ROUNDED` | Rounded corners |
| `ASCII` | ASCII characters (+, -, |) |

---

## Class: `BorderChars`

Characters for drawing a border.

### Constructor

```python
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
```

### Static Methods

#### `for_style`
```python
@staticmethod
def for_style(style: BorderStyle) -> BorderChars
```
Get the border characters for a given style.

**Parameters:**
- `style` (`BorderStyle`): The border style

**Returns:** `BorderChars` - The characters for that style

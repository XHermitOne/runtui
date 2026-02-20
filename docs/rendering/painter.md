# rendering/painter.py - Painter

Clipped drawing API for widgets.

---

## Class: `Painter`

A clipped drawing surface for a widget. All coordinates are relative to the clip region's origin. Drawing outside the clip region is silently clipped.

### Constructor

```python
def __init__(
    self,
    buffer: CellBuffer,
    clip: Rect,
    offset: Point | None = None,
) -> None
```

**Parameters:**
- `buffer` (`CellBuffer`): The cell buffer to draw on
- `clip` (`Rect`): The clipping rectangle
- `offset` (`Point | None`): Offset for coordinate conversion

### Properties

#### `width`
```python
@property
def width(self) -> int
```
Returns the clip region width.

#### `height`
```python
@property
def height(self) -> int
```
Returns the clip region height.

### Drawing Methods

#### `put_char`
```python
def put_char(
    self,
    x: int,
    y: int,
    char: str,
    fg: Color = Color.DEFAULT,
    bg: Color = Color.DEFAULT,
    attrs: Attrs = Attrs.NONE,
) -> None
```
Put a single character at the given position.

**Parameters:**
- `x` (`int`): Local X coordinate
- `y` (`int`): Local Y coordinate
- `char` (`str`): The character
- `fg` (`Color`): Foreground color
- `bg` (`Color`): Background color
- `attrs` (`Attrs`): Text attributes

#### `put_str`
```python
def put_str(
    self,
    x: int,
    y: int,
    text: str,
    fg: Color = Color.DEFAULT,
    bg: Color = Color.DEFAULT,
    attrs: Attrs = Attrs.NONE,
    max_width: int | None = None,
) -> int
```
Write text at position.

**Parameters:**
- `x` (`int`): Local X coordinate
- `y` (`int`): Local Y coordinate
- `text` (`str`): The text to write
- `fg` (`Color`): Foreground color
- `bg` (`Color`): Background color
- `attrs` (`Attrs`): Text attributes
- `max_width` (`int | None`): Maximum width (truncates if exceeded)

**Returns:** `int` - Display width written

#### `fill_rect`
```python
def fill_rect(
    self,
    x: int,
    y: int,
    width: int,
    height: int,
    char: str = " ",
    fg: Color = Color.DEFAULT,
    bg: Color = Color.DEFAULT,
    attrs: Attrs = Attrs.NONE,
) -> None
```
Fill a rectangle with a character.

**Parameters:**
- `x` (`int`): Local X coordinate
- `y` (`int`): Local Y coordinate
- `width` (`int`): Rectangle width
- `height` (`int`): Rectangle height
- `char` (`str`): Fill character (default: space)
- `fg` (`Color`): Foreground color
- `bg` (`Color`): Background color
- `attrs` (`Attrs`): Text attributes

#### `draw_border`
```python
def draw_border(
    self,
    x: int,
    y: int,
    width: int,
    height: int,
    style: BorderStyle = BorderStyle.SINGLE,
    fg: Color = Color.DEFAULT,
    bg: Color = Color.DEFAULT,
    attrs: Attrs = Attrs.NONE,
) -> None
```
Draw a border around a rectangle.

**Parameters:**
- `x` (`int`): Local X coordinate
- `y` (`int`): Local Y coordinate
- `width` (`int`): Rectangle width
- `height` (`int`): Rectangle height
- `style` (`BorderStyle`): Border style
- `fg` (`Color`): Foreground color
- `bg` (`Color`): Background color
- `attrs` (`Attrs`): Text attributes

#### `draw_hline`
```python
def draw_hline(
    self,
    x: int,
    y: int,
    width: int,
    char: str = "─",
    fg: Color = Color.DEFAULT,
    bg: Color = Color.DEFAULT,
    attrs: Attrs = Attrs.NONE,
) -> None
```
Draw a horizontal line.

**Parameters:**
- `x` (`int`): Starting X coordinate
- `y` (`int`): Y coordinate
- `width` (`int`): Line width
- `char` (`str`): Line character
- `fg` (`Color`): Foreground color
- `bg` (`Color`): Background color
- `attrs` (`Attrs`): Text attributes

#### `draw_vline`
```python
def draw_vline(
    self,
    x: int,
    y: int,
    height: int,
    char: str = "│",
    fg: Color = Color.DEFAULT,
    bg: Color = Color.DEFAULT,
    attrs: Attrs = Attrs.NONE,
) -> None
```
Draw a vertical line.

**Parameters:**
- `x` (`int`): X coordinate
- `y` (`int`): Starting Y coordinate
- `height` (`int`): Line height
- `char` (`str`): Line character
- `fg` (`Color`): Foreground color
- `bg` (`Color`): Background color
- `attrs` (`Attrs`): Text attributes

#### `sub_painter`
```python
def sub_painter(
    self,
    x: int,
    y: int,
    width: int,
    height: int,
) -> Painter
```
Create a sub-painter clipped to a sub-region.

**Parameters:**
- `x` (`int`): Sub-region X offset
- `y` (`int`): Sub-region Y offset
- `width` (`int`): Sub-region width
- `height` (`int`): Sub-region height

**Returns:** `Painter` - A new painter clipped to the sub-region
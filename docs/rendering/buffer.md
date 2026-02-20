# rendering/buffer.py - Cell Buffer

A 2D grid of terminal cells for rendering.

---

## Class: `CellBuffer`

A 2D grid of terminal cells.

### Constructor

```python
def __init__(self, width: int, height: int) -> None
```

**Parameters:**
- `width` (`int`): Buffer width in columns
- `height` (`int`): Buffer height in rows

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `width` | `int` | Buffer width in columns |
| `height` | `int` | Buffer height in rows |

### Methods

#### `get`
```python
def get(self, x: int, y: int) -> Cell
```
Get the cell at position (x, y). Returns an empty cell if out of bounds.

**Parameters:**
- `x` (`int`): Column position
- `y` (`int`): Row position

**Returns:** `Cell` - The cell at that position

#### `set`
```python
def set(self, x: int, y: int, cell: Cell) -> None
```
Set the cell at position (x, y).

**Parameters:**
- `x` (`int`): Column position
- `y` (`int`): Row position
- `cell` (`Cell`): The cell to copy

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
) -> int
```
Put a character at position (x, y). Handles wide characters automatically.

**Parameters:**
- `x` (`int`): Column position
- `y` (`int`): Row position
- `char` (`str`): The character to put
- `fg` (`Color`): Foreground color
- `bg` (`Color`): Background color
- `attrs` (`Attrs`): Text attributes

**Returns:** `int` - The display width consumed (1 or 2)

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
) -> int
```
Write a string starting at position (x, y).

**Parameters:**
- `x` (`int`): Starting column
- `y` (`int`): Row position
- `text` (`str`): The text to write
- `fg` (`Color`): Foreground color
- `bg` (`Color`): Background color
- `attrs` (`Attrs`): Text attributes

**Returns:** `int` - The display width used

#### `fill_rect`
```python
def fill_rect(
    self,
    rect: Rect,
    char: str = " ",
    fg: Color = Color.DEFAULT,
    bg: Color = Color.DEFAULT,
    attrs: Attrs = Attrs.NONE,
) -> None
```
Fill a rectangle with a character.

**Parameters:**
- `rect` (`Rect`): The rectangle to fill
- `char` (`str`): Fill character
- `fg` (`Color`): Foreground color
- `bg` (`Color`): Background color
- `attrs` (`Attrs`): Text attributes

#### `clear`
```python
def clear(
    self,
    fg: Color = Color.DEFAULT,
    bg: Color = Color.DEFAULT,
) -> None
```
Clear the entire buffer.

**Parameters:**
- `fg` (`Color`): Foreground color for cleared cells
- `bg` (`Color`): Background color for cleared cells

#### `resize`
```python
def resize(self, width: int, height: int) -> None
```
Resize the buffer, preserving content where possible.

**Parameters:**
- `width` (`int`): New width
- `height` (`int`): New height

#### `copy_from`
```python
def copy_from(self, other: CellBuffer) -> None
```
Copy contents from another buffer.

**Parameters:**
- `other` (`CellBuffer`): Source buffer
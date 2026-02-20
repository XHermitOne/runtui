# mouse/cursor.py - Mouse Cursor

Software mouse cursor rendering.

---

## Class: `SoftwareCursor`

A software-rendered mouse cursor.

### Constructor

```python
def __init__(self, shape: str = "block") -> None
```

**Parameters:**
- `shape` (`str`): Cursor shape: `"block"`, `"underline"`, or `"beam"`

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `x` | `int` | Cursor X position |
| `y` | `int` | Cursor Y position |
| `visible` | `bool` | Whether cursor is visible |
| `shape` | `str` | Cursor shape |

### Methods

#### `move_to`
```python
def move_to(self, x: int, y: int) -> None
```
Move cursor to position.

**Parameters:**
- `x` (`int`): Column position
- `y` (`int`): Row position

#### `show` / `hide`
```python
def show(self) -> None
def hide(self) -> None
```
Show or hide the cursor.

#### `paint`
```python
def paint(self, painter: Painter) -> None
```
Paint the cursor onto the buffer.

**Parameters:**
- `painter` (`Painter`): The painter to draw with
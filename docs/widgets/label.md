# widgets/label.py - Label Widget

Static text display widget.

---

## Class: `Label`

Displays static text.

### Constructor

```python
def __init__(
    self,
    text: str = "",
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 0,
    height: int = 1,
    align: str = "left",
    fg: Color | None = None,
    bg: Color | None = None,
    bold: bool = False,
) -> None
```

**Parameters:**
- `text` (`str`): The text to display
- `id` (`str | None`): Widget identifier
- `x` (`int`): X position
- `y` (`int`): Y position
- `width` (`int`): Width (0 = auto-size to text)
- `height` (`int`): Height
- `align` (`str`): Text alignment: `"left"`, `"center"`, or `"right"`
- `fg` (`Color | None`): Foreground color
- `bg` (`Color | None`): Background color
- `bold` (`bool`): Whether text is bold

### Properties

#### `text`
```python
@property
def text(self) -> str
```
Get the label text.

```python
@text.setter
def text(self, value: str) -> None
```
Set the label text.

### Methods

#### `measure`
```python
def measure(self, available: Size) -> Size
```
Return the size needed to display the text.

#### `paint`
```python
def paint(self, painter: Painter) -> None
```
Draw the label text.

### Theme Colors

| Slot | Description |
|------|-------------|
| `label.fg` | Text color |
| `label.bg` | Background color |

### Usage

```python
# Simple label
label = Label("Hello, World!")

# Centered label with custom colors
label = Label(
    "Title",
    width=20,
    align="center",
    fg=Color.WHITE,
    bg=Color.BLUE,
    bold=True,
)
```
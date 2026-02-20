# widgets/button.py - Button Widget

A clickable button with a label.

---

## Class: `Button`

A clickable button widget.

### Constructor

```python
def __init__(
    self,
    text: str = "Button",
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 0,
    height: int = 1,
    on_click: Callable[[], None] | None = None,
) -> None
```

**Parameters:**
- `text` (`str`): Button label text
- `id` (`str | None`): Widget identifier
- `x` (`int`): X position
- `y` (`int`): Y position
- `width` (`int`): Width (0 = auto-size)
- `height` (`int`): Height
- `on_click` (`Callable[[], None] | None`): Click callback

### Properties

#### `text`
```python
@property
def text(self) -> str
```
Get the button text.

```python
@text.setter
def text(self, value: str) -> None
```
Set the button text.

### Methods

#### `measure`
```python
def measure(self, available: Size) -> Size
```
Return the size needed (text + 4 for "[ text ]" formatting).

#### `paint`
```python
def paint(self, painter: Painter) -> None
```
Draw the button with its label.

### Events

The button handles:
- **Mouse click**: Press and release triggers click
- **Enter/Space key**: Triggers click when focused

### Theme Colors

| Slot | Description |
|------|-------------|
| `button.fg` | Normal text color |
| `button.bg` | Normal background |
| `button.focused.fg` | Focused text color |
| `button.focused.bg` | Focused background |
| `button.pressed.fg` | Pressed text color |
| `button.pressed.bg` | Pressed background |

### Usage

```python
def handle_click():
    print("Button clicked!")

button = Button("Click Me", on_click=handle_click)
```

Or use event binding:

```python
button = Button("Click Me")
button.on(MouseEvent, lambda e: print("Clicked!") if e.action == MouseAction.RELEASE else None)
```
# layout/absolute.py - Absolute Layout

Layout where children are positioned manually.

---

## Class: `AbsoluteLayout`

Layout where each child specifies its own x, y, width, and height.

Stores the original relative positions on first arrange so that repeated calls to arrange() don't compound the container offset.

### Constructor

```python
def __init__(self) -> None
```

### Methods

#### `measure`
```python
def measure(self, container: Widget, available: Size) -> Size
```
Returns the available size.

**Parameters:**
- `container` (`Widget`): The container widget
- `available` (`Size`): Available size

**Returns:** `Size` - The available size

#### `arrange`
```python
def arrange(self, container: Widget, rect: Rect) -> None
```
Position children at their specified coordinates.

Children should have `x`, `y`, `width`, and `height` attributes set before arranging.

**Parameters:**
- `container` (`Widget`): The container widget
- `rect` (`Rect`): The container's rectangle

### Usage

```python
container = Container(layout=AbsoluteLayout())
button = Button("Click", x=10, y=5, width=15, height=3)
container.add(button)
```
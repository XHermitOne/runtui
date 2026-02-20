# widgets/container.py - Container Widget

A widget that contains and manages child widgets.

---

## Class: `Container`

A widget that contains and manages child widgets. Can optionally draw a border and title.

### Constructor

```python
def __init__(
    self,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 0,
    height: int = 0,
    border: BorderStyle = BorderStyle.NONE,
    title: str = "",
) -> None
```

**Parameters:**
- `id` (`str | None`): Widget identifier
- `x` (`int`): X position
- `y` (`int`): Y position
- `width` (`int`): Width
- `height` (`int`): Height
- `border` (`BorderStyle`): Border style
- `title` (`str`): Title text displayed in border

### Properties

#### `has_border`
```python
@property
def has_border(self) -> bool
```
Returns True if the container has a border.

#### `content_rect`
```python
@property
def content_rect(self) -> Rect
```
Returns the rect for child content, inset by border if present.

### Methods

#### `arrange`
```python
def arrange(self, rect: Rect) -> None
```
Position the container and arrange children using the layout manager.

#### `paint`
```python
def paint(self, painter: Painter) -> None
```
Draw the container background, border, and title.

### Layout

Containers can have a layout manager set via `_layout_manager`:

```python
container = Container(border=BorderStyle.SINGLE, title="Settings")
container._layout_manager = VBoxLayout(spacing=1)
container.add_child(Label("Name:"))
container.add_child(TextInput())
```

### Theme Colors

| Slot | Description |
|------|-------------|
| `container.bg` | Background color |
| `container.fg` | Foreground color |
| `container.border` | Border color |
| `container.title` | Title text color |
# widgets/base.py - Widget Base Class

Base class for all TUI widgets.

---

## Class: `Widget`

Base class for all TUI widgets. Inherits from `EventMixin` for event handling.

### Constructor

```python
def __init__(
    self,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 0,
    height: int = 0,
) -> None
```

**Parameters:**
- `id` (`str | None`): Optional widget identifier
- `x` (`int`): X position relative to parent
- `y` (`int`): Y position relative to parent
- `width` (`int`): Widget width (0 = auto)
- `height` (`int`): Widget height (0 = auto)

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str \| None` | Widget identifier |
| `classes` | `set[str]` | CSS-like class names |
| `parent` | `Widget \| None` | Parent widget |
| `children` | `list[Widget]` | Child widgets |
| `x`, `y` | `int` | Position relative to parent |
| `width`, `height` | `int` | Size |
| `min_width`, `min_height` | `int` | Minimum size constraints |
| `max_width`, `max_height` | `int` | Maximum size constraints |
| `dock` | `str` | Dock position for DockLayout |
| `flex` | `float` | Flex factor for box layouts |
| `visible` | `bool` | Whether widget is visible |
| `enabled` | `bool` | Whether widget is enabled |
| `can_focus` | `bool` | Whether widget can receive focus |

### Properties

#### `focused`
```python
@property
def focused(self) -> bool
```
Returns True if this widget has focus.

#### `screen_rect`
```python
@property
def screen_rect(self) -> Rect
```
Returns the absolute screen rectangle.

#### `content_rect`
```python
@property
def content_rect(self) -> Rect
```
Returns the content area (inside borders/padding).

### Tree Operations

#### `add_child`
```python
def add_child(self, child: Widget) -> None
```
Add a child widget.

#### `remove_child`
```python
def remove_child(self, child: Widget) -> None
```
Remove a child widget.

#### `clear_children`
```python
def clear_children(self) -> None
```
Remove all children.

#### `find_by_id`
```python
def find_by_id(self, widget_id: str) -> Widget | None
```
Find a widget by ID in this subtree.

#### `ancestors`
```python
def ancestors(self) -> list[Widget]
```
Get list of ancestors from parent to root.

#### `root`
```python
def root(self) -> Widget
```
Get the root widget of this tree.

### Layout

#### `measure`
```python
def measure(self, available: Size) -> Size
```
Return desired size given available space. Override in subclasses.

#### `arrange`
```python
def arrange(self, rect: Rect) -> None
```
Position this widget within the given rect.

#### `layout_if_needed`
```python
def layout_if_needed(self) -> None
```
Recursively layout if dirty.

#### `invalidate`
```python
def invalidate(self) -> None
```
Mark for repaint.

#### `invalidate_layout`
```python
def invalidate_layout(self) -> None
```
Mark for re-layout and repaint.

### Painting

#### `paint`
```python
def paint(self, painter: Painter) -> None
```
Draw this widget. Override in subclasses.

#### `paint_if_needed`
```python
def paint_if_needed(self, painter: Painter) -> None
```
Recursively paint if dirty.

#### `get_painter`
```python
def get_painter(self, parent_painter: Painter) -> Painter
```
Get a painter clipped to this widget's area.

### Focus

#### `focus`
```python
def focus(self) -> None
```
Give this widget focus.

#### `blur`
```python
def blur(self) -> None
```
Remove focus from this widget.

#### `focus_next`
```python
def focus_next(self) -> Widget | None
```
Move focus to next focusable widget. Returns the newly focused widget.

#### `focus_prev`
```python
def focus_prev(self) -> Widget | None
```
Move focus to previous focusable widget.

### Hit Testing

#### `hit_test`
```python
def hit_test(self, x: int, y: int) -> Widget | None
```
Return deepest widget at screen coordinates.

### Theme

#### `get_theme`
```python
def get_theme(self) -> ThemeEngine | None
```
Walk up tree to find the theme engine.

#### `theme_color`
```python
def theme_color(self, slot: str, fallback: Color = Color.DEFAULT) -> Color
```
Get a color from the current theme.

#### `theme_glyph`
```python
def theme_glyph(self, slot: str, fallback: str = "") -> str
```
Get a glyph from the current theme.

---

## Helper Functions

### `_find_focused`
```python
def _find_focused(widget: Widget) -> Widget | None
```
Find the currently focused widget in the tree.

### `_collect_focusable`
```python
def _collect_focusable(root: Widget) -> list[Widget]
```
Collect all focusable widgets in depth-first order.
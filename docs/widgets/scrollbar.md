# widgets/scrollbar.py - Scrollbar Widgets

Horizontal and vertical scrollbars.

---

## Class: `VScrollbar`

Vertical scrollbar widget.

### Constructor

```python
def __init__(
    self,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    height: int = 10,
    total: int = 100,
    visible_amount: int = 10,
    value: int = 0,
    on_change: Callable[[int], None] | None = None,
) -> None
```

**Parameters:**
- `height` (`int`): Height in rows
- `total` (`int`): Total range
- `visible_amount` (`int`): Visible portion size
- `value` (`int`): Current scroll position
- `on_change` (`Callable[[int], None]`): Callback when value changes

### Properties

#### `value`
```python
@property
def value(self) -> int
```
Current scroll position.

### Methods

#### `set_range`
```python
def set_range(self, total: int, visible_amount: int) -> None
```
Update the scrollbar range.

---

## Class: `HScrollbar`

Horizontal scrollbar widget.

### Constructor

```python
def __init__(
    self,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 20,
    total: int = 100,
    visible_amount: int = 10,
    value: int = 0,
    on_change: Callable[[int], None] | None = None,
) -> None
```

Same parameters as `VScrollbar` but for horizontal orientation.

### Theme Glyphs

| Slot | Default |
|------|---------|
| `scrollbar.track` | `░` |
| `scrollbar.thumb` | `█` |
| `scrollbar.up` | `▲` |
| `scrollbar.down` | `▼` |
| `scrollbar.left` | `◄` |
| `scrollbar.right` | `►` |
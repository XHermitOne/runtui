# widgets/color_picker.py - ColorPicker Widget

Color selection widget.

---

## Class: `ColorPicker`

A color picker widget for selecting colors.

### Constructor

```python
def __init__(
    self,
    color: Color | None = None,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    on_change: Callable[[Color], None] | None = None,
) -> None
```

**Parameters:**
- `color` (`Color | None`): Initial color
- `on_change` (`Callable[[Color], None]`): Callback when color changes

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `color` | `Color` | Selected color |

### Methods

#### `set_color`
```python
def set_color(self, r: int, g: int, b: int) -> None
```
Set the color from RGB values.

### Key Bindings

| Key | Action |
|-----|--------|
| Arrow keys | Adjust color components |
| Tab | Switch between R/G/B components |
| Enter | Confirm selection |
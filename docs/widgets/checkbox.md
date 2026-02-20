# widgets/checkbox.py - Checkbox Widget

A checkbox with a label.

---

## Class: `Checkbox`

A checkbox widget that can be toggled on/off.

### Constructor

```python
def __init__(
    self,
    label: str = "",
    checked: bool = False,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 0,
    on_change: Callable[[bool], None] | None = None,
) -> None
```

**Parameters:**
- `label` (`str`): Label text
- `checked` (`bool`): Initial checked state
- `on_change` (`Callable[[bool], None]`): Callback when state changes

### Properties

#### `checked`
```python
@property
def checked(self) -> bool
```
Get or set the checked state.

### Methods

#### `toggle`
```python
def toggle(self) -> None
```
Toggle the checked state.

### Theme Glyphs

| Slot | Default |
|------|---------|
| `checkbox.checked` | `[X]` |
| `checkbox.unchecked` | `[ ]` |

### Usage

```python
checkbox = Checkbox("Enable feature", checked=True, on_change=lambda v: print(v))
```
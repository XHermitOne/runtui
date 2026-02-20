# widgets/dropdown.py - DropDownList Widget

Dropdown selection widget.

---

## Class: `DropDownList`

A dropdown list that shows options when clicked.

### Constructor

```python
def __init__(
    self,
    items: list[str] | None = None,
    selected_index: int = -1,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 20,
    on_change: Callable[[int, str], None] | None = None,
) -> None
```

**Parameters:**
- `items` (`list[str]`): List of options
- `selected_index` (`int`): Initially selected index (-1 for none)
- `on_change` (`Callable[[int, str], None]`): Callback when selection changes

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `items` | `list[str]` | List of options |
| `selected_index` | `int` | Selected index |
| `selected_item` | `str \| None` | Selected item text |

### Usage

```python
dropdown = DropDownList(
    items=["Option 1", "Option 2", "Option 3"],
    on_change=lambda i, s: print(f"Selected: {s}")
)
```
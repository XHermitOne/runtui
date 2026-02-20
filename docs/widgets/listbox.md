# widgets/listbox.py - ListBox Widget

Scrollable list of selectable items.

---

## Class: `ListBox`

A scrollable list of items with selection support. Supports optional multi-selection.

### Constructor

```python
def __init__(
    self,
    items: list[str] | None = None,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 20,
    height: int = 8,
    on_select: Callable[[int, str], None] | None = None,
    on_activate: Callable[[int, str], None] | None = None,
    multi_select: bool = False,
) -> None
```

**Parameters:**
- `items` (`list[str]`): List of item strings
- `on_select` (`Callable[[int, str], None]`): Callback when selection changes
- `on_activate` (`Callable[[int, str], None]`): Callback when item is activated (double-click or Enter)
- `multi_select` (`bool`): Enable multi-selection mode

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `items` | `list[str]` | List of items |
| `selected_index` | `int` | Currently selected index |
| `selected_item` | `str \| None` | Currently selected item text |
| `selected_indices` | `set[int]` | Selected indices (multi-select mode) |

### Methods

#### `add_item`
```python
def add_item(self, item: str) -> None
```
Add an item to the list.

#### `remove_item`
```python
def remove_item(self, index: int) -> None
```
Remove an item by index.

#### `clear`
```python
def clear(self) -> None
```
Clear all items.

#### `clear_selection`
```python
def clear_selection(self) -> None
```
Clear all selections in multi-select mode.

### Key Bindings

| Key | Action |
|-----|--------|
| Up/Down | Move selection |
| Home/End | First/last item |
| Page Up/Down | Scroll by page |
| Enter | Activate item |

### Multi-Select

When `multi_select=True`:
- **Shift+Click**: Range selection
- **Ctrl+Click**: Toggle individual item
- **Shift+Arrow**: Extend selection
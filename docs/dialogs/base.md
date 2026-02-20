# dialogs/base.py - Base Dialog

Base class for modal dialogs.

---

## Class: `Dialog`

Modal dialog base class. Dialogs are centered windows with OK/Cancel buttons. When shown modally, they capture all input until dismissed.

### Constructor

```python
def __init__(
    self,
    title: str = "Dialog",
    width: int = 40,
    height: int = 12,
    id: str | None = None,
) -> None
```

**Parameters:**
- `title` (`str`): Dialog title
- `width` (`int`): Dialog width
- `height` (`int`): Dialog height

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `result` | `Any` | Dialog result (set on close) |
| `closed` | `bool` | Whether dialog has been closed |

### Methods

#### `center_on_screen`
```python
def center_on_screen(self, screen_width: int, screen_height: int) -> None
```
Center the dialog on screen.

#### `close`
```python
def close(self, result: Any = None) -> None
```
Close the dialog with an optional result.

### Key Bindings

| Key | Action |
|-----|--------|
| Escape | Close dialog with None result |
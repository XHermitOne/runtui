# windows/window.py - Window Widget

Top-level window widget with title bar and chrome.

---

## Enum: `WindowState`

Window state.

| Value | Description |
|-------|-------------|
| `NORMAL` | Normal windowed state |
| `MINIMIZED` | Minimized to taskbar |
| `MAXIMIZED` | Maximized to fill desktop |

---

## Class: `Window`

A top-level window with title bar, borders, and window controls.

### Constructor

```python
def __init__(
    self,
    title: str = "Window",
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 60,
    height: int = 20,
    can_minimize: bool = True,
    can_maximize: bool = True,
    can_close: bool = True,
    can_resize: bool = True,
) -> None
```

**Parameters:**
- `title` (`str`): Window title
- `can_minimize` (`bool`): Show minimize button
- `can_maximize` (`bool`): Show maximize button
- `can_close` (`bool`): Show close button
- `can_resize` (`bool`): Allow resizing

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `title` | `str` | Window title |
| `state` | `WindowState` | Current state |
| `is_active` | `bool` | Whether this is the active window |

### Methods

#### `restore`
```python
def restore(self) -> None
```
Restore from minimized/maximized state.

#### `close`
```python
def close(self) -> None
```
Close the window.

### Content

Add child widgets to the window's content area:

```python
window = Window(title="My Window")
window.add_child(Label("Hello, World!"))
```

### Window Chrome

The window automatically draws:
- Title bar with title text
- Minimize button (`_`)
- Maximize button (`^`)
- Close button (`X`)
- Borders and shadow
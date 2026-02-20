# windows/taskbar.py - Taskbar Widget

Desktop taskbar showing open windows.

---

## Class: `Taskbar`

A taskbar widget that displays buttons for open windows.

### Constructor

```python
def __init__(
    self,
    window_manager: WindowManager,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 0,
) -> None
```

**Parameters:**
- `window_manager` (`WindowManager`): The window manager to track
- `width` (`int`): Width (0 = full screen width)

### Features

- Displays a button for each open window
- Click a button to activate that window
- Shows window title in the button
- Highlights the active window button
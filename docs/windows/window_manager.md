# windows/window_manager.py - Window Manager

Manages multiple windows with z-ordering, focus, and layout.

---

## Class: `WindowManager`

Manages multiple windows: z-order, focus, move, minimize/maximize/close.

### Constructor

```python
def __init__(self, screen_width: int, screen_height: int) -> None
```

**Parameters:**
- `screen_width` (`int`): Screen width in columns
- `screen_height` (`int`): Screen height in rows

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `windows` | `list[Window]` | All windows in z-order (bottom to top) |
| `visible_windows` | `list[Window]` | Visible windows only |
| `active_window` | `Window \| None` | Currently active (focused) window |
| `desktop_rect` | `Rect` | Available area for windows (between menu and taskbar) |

### Methods

#### `resize_screen`
```python
def resize_screen(self, width: int, height: int) -> None
```
Handle screen resize, updating all window bounds.

**Parameters:**
- `width` (`int`): New screen width
- `height` (`int`): New screen height

#### `add_window`
```python
def add_window(self, window: Window, activate: bool = True) -> None
```
Add a window. Cascades position if at defaults.

**Parameters:**
- `window` (`Window`): The window to add
- `activate` (`bool`): Whether to bring to front

#### `remove_window`
```python
def remove_window(self, window: Window) -> None
```
Remove a window.

**Parameters:**
- `window` (`Window`): The window to remove

#### `activate`
```python
def activate(self, window: Window) -> None
```
Bring window to front and give it focus.

**Parameters:**
- `window` (`Window`): The window to activate

#### `bring_to_front`
```python
def bring_to_front(self, window: Window) -> None
```
Bring window to top of z-order (same as activate).

#### `minimize`
```python
def minimize(self, window: Window) -> None
```
Minimize a window.

#### `maximize`
```python
def maximize(self, window: Window) -> None
```
Maximize a window to fill the desktop area.

#### `restore`
```python
def restore(self, window: Window) -> None
```
Restore a window from minimized/maximized state.

#### `close`
```python
def close(self, window: Window) -> None
```
Close and remove a window.

#### `cycle_next`
```python
def cycle_next(self) -> None
```
Cycle to next window in z-order (Alt+Tab behavior).

#### `cycle_prev`
```python
def cycle_prev(self) -> None
```
Cycle to previous window in z-order (Alt+Shift+Tab behavior).

#### `cascade`
```python
def cascade(self) -> None
```
Arrange all visible windows in a cascade pattern.

#### `tile_horizontal`
```python
def tile_horizontal(self) -> None
```
Tile windows side by side horizontally.

#### `tile_vertical`
```python
def tile_vertical(self) -> None
```
Tile windows stacked vertically.

#### `hit_test`
```python
def hit_test(self, x: int, y: int) -> Window | None
```
Find topmost window at screen position.

**Parameters:**
- `x` (`int`): X coordinate
- `y` (`int`): Y coordinate

**Returns:** `Window | None` - The window at that position

#### `handle_mouse`
```python
def handle_mouse(self, event: MouseEvent) -> bool
```
Route mouse event to appropriate window.

**Parameters:**
- `event` (`MouseEvent`): The mouse event

**Returns:** `bool` - True if handled

#### `paint`
```python
def paint(self, painter: Painter) -> None
```
Paint all visible windows in z-order (bottom to top).

### Z-Order

Windows are stored in z-order with index 0 at the bottom. When a window is activated, it's moved to the end of the list (top).

### Auto-Cascade

When adding a window at default position (x ≤ 2, y ≤ 1), the manager automatically positions it in a cascade pattern, offset by (2, 1) from the previous window.

### Window Events

The manager listens for WindowEvent on each window:
- `WindowAction.CLOSE`: Removes the window
- `WindowAction.MAXIMIZE`: Resizes to desktop bounds
- `WindowAction.MINIMIZE`: Activates next window

### Dropdown Overlays

The manager collects expanded dropdown widgets during painting and renders them on top of all window content to ensure proper overlay behavior.

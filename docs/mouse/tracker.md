# mouse/tracker.py - Mouse Tracker

Mouse event tracking and gesture detection.

---

## Class: `MouseTracker`

Tracks mouse state and detects gestures.

### Constructor

```python
def __init__(self) -> None
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `last_pos` | `Point` | Last mouse position |
| `last_button` | `MouseButton` | Last button pressed |
| `last_action` | `MouseAction` | Last action |
| `drag_start` | `Point \| None` | Drag start position |
| `is_dragging` | `bool` | Whether a drag is in progress |

### Methods

#### `update`
```python
def update(self, event: MouseEvent) -> None
```
Update tracker state from a mouse event.

**Parameters:**
- `event` (`MouseEvent`): The mouse event

#### `is_click`
```python
def is_click(
    self,
    event: MouseEvent,
    max_distance: int = 3,
    max_time: float = 0.5,
) -> bool
```
Check if an event represents a click (not a drag).

**Parameters:**
- `event` (`MouseEvent`): Release event
- `max_distance` (`int`): Maximum pixels from press position
- `max_time` (`float`): Maximum seconds since press

**Returns:** `bool` - True if this is a click

#### `is_double_click`
```python
def is_double_click(
    self,
    event: MouseEvent,
    max_time: float = 0.3,
) -> bool
```
Check if this is a double-click.

**Parameters:**
- `event` (`MouseEvent`): The press event
- `max_time` (`float`): Maximum seconds since last click

**Returns:** `bool` - True if this is a double-click
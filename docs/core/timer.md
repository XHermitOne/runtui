# timer.py - Timer and Interval Support

Timer and interval management for the event loop.

---

## Class: `TimerHandle`

A handle to a scheduled timer that can be cancelled.

### Constructor

```python
@dataclass
class TimerHandle:
    callback: Callable[[], None]
    fire_at: float
    interval: float = 0.0  # 0 = one-shot, >0 = repeating
    cancelled: bool = False
    _id: int = 0
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `callback` | `Callable[[], None]` | Function to call when timer fires |
| `fire_at` | `float` | Monotonic time when timer should fire |
| `interval` | `float` | 0 for one-shot, >0 for repeating interval |
| `cancelled` | `bool` | Whether the timer has been cancelled |

### Methods

#### `cancel`
```python
def cancel(self) -> None
```
Cancel the timer so it won't fire.

---

## Class: `TimerManager`

Manages timers and intervals.

### Methods

#### `call_later`
```python
def call_later(
    self,
    delay: float,
    callback: Callable[[], None],
) -> TimerHandle
```

Schedule a one-shot callback after a delay.

**Parameters:**
- `delay` (`float`): Delay in seconds
- `callback` (`Callable[[], None]`): Function to call

**Returns:** `TimerHandle` - Handle to cancel the timer

#### `set_interval`
```python
def set_interval(
    self,
    interval: float,
    callback: Callable[[], None],
) -> TimerHandle
```

Schedule a repeating callback at the given interval.

**Parameters:**
- `interval` (`float`): Interval in seconds
- `callback` (`Callable[[], None]`): Function to call

**Returns:** `TimerHandle` - Handle to cancel the timer

#### `process`
```python
def process(self) -> None
```
Fire any timers that are due. Called from the event loop each frame.

#### `cancel_all`
```python
def cancel_all(self) -> None
```
Cancel all active timers.

#### `next_deadline`
```python
@property
def next_deadline(self) -> float | None
```

Get the time until the next timer fires.

**Returns:** `float | None` - Seconds until next timer, or None if no timers
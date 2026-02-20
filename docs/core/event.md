# event.py - Event System

Event base classes, typed events, and dispatch system for the runtui framework.

---

## Enum: `Phase`

Event propagation phase.

| Value | Description |
|-------|-------------|
| `TUNNEL` | Traveling from root to target |
| `BUBBLE` | Traveling from target back to root |

---

## Enum: `Strategy`

Event dispatch strategy.

| Value | Description |
|-------|-------------|
| `TUNNEL_THEN_BUBBLE` | Full propagation: tunnel down then bubble up |
| `DIRECT` | Deliver directly to target only |
| `BROADCAST` | Deliver to target and all descendants |

---

## Class: `Event`

Base class for all events.

### Constructor

```python
@dataclass
class Event:
    timestamp: float = field(default_factory=time.monotonic)
    handled: bool = False
    cancelled: bool = False
    _propagation_stopped: bool = field(default=False, repr=False)
```

### Methods

#### `stop_propagation`
```python
def stop_propagation(self) -> None
```
Stop the event from propagating further.

#### `prevent_default`
```python
def prevent_default(self) -> None
```
Mark the event as cancelled (prevent default behavior).

#### `mark_handled`
```python
def mark_handled(self) -> None
```
Mark the event as handled and stop propagation.

---

## Class: `InputEvent`

Base class for user-input events (keyboard, mouse).

```python
class InputEvent(Event):
    pass
```

---

## Class: `KeyEvent`

Keyboard input event.

### Constructor

```python
@dataclass
class KeyEvent(InputEvent):
    key: Keys = Keys.UNKNOWN
    char: str = ""
    modifiers: Modifiers = Modifiers.NONE
    is_repeat: bool = False
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `key` | `Keys` | The key that was pressed |
| `char` | `str` | The character (if `key == Keys.CHAR`) |
| `modifiers` | `Modifiers` | Active modifier flags |
| `is_repeat` | `bool` | True if this is a key repeat |

---

## Class: `MouseEvent`

Mouse input event.

### Constructor

```python
@dataclass
class MouseEvent(InputEvent):
    x: int = 0
    y: int = 0
    button: MouseButton = MouseButton.NONE
    action: MouseAction = MouseAction.MOVE
    modifiers: Modifiers = Modifiers.NONE
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `x` | `int` | X coordinate |
| `y` | `int` | Y coordinate |
| `button` | `MouseButton` | The button involved |
| `action` | `MouseAction` | The type of action |
| `modifiers` | `Modifiers` | Active modifier flags |

---

## Class: `FocusEvent`

Focus change event.

### Constructor

```python
@dataclass
class FocusEvent(Event):
    gained: bool = True
    previous: Any = None
    next: Any = None
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `gained` | `bool` | True if focus was gained, False if lost |
| `previous` | `Any` | Previously focused widget |
| `next` | `Any` | Newly focused widget |

---

## Enum: `WindowAction`

Window action types.

| Value | Description |
|-------|-------------|
| `CLOSE` | Window is closing |
| `MINIMIZE` | Window is being minimized |
| `MAXIMIZE` | Window is being maximized |
| `RESTORE` | Window is being restored |
| `MOVE` | Window is being moved |
| `RESIZE` | Window is being resized |
| `ACTIVATE` | Window is becoming active |
| `DEACTIVATE` | Window is losing activation |

---

## Class: `WindowEvent`

Window-related event.

### Constructor

```python
@dataclass
class WindowEvent(Event):
    action: WindowAction = WindowAction.CLOSE
    window: Any = None
```

---

## Class: `ResizeEvent`

Terminal resize event.

### Constructor

```python
@dataclass
class ResizeEvent(Event):
    width: int = 0
    height: int = 0
```

---

## Class: `ThemeChangedEvent`

Theme change notification event.

### Constructor

```python
@dataclass
class ThemeChangedEvent(Event):
    theme_name: str = ""
```

---

## Class: `CustomEvent`

User-defined custom event.

### Constructor

```python
@dataclass
class CustomEvent(Event):
    name: str = ""
    data: Any = None
```

---

## Class: `Subscription`

Handle for removing an event handler.

### Methods

#### `dispose`
```python
def dispose(self) -> None
```
Remove the registered handler.

---

## Class: `EventMixin`

Mixin that provides event handler registration to any class.

### Methods

#### `on`
```python
def on(
    self,
    event_type: type[Event],
    handler: Callable[[Event], None],
    phase: Phase = Phase.BUBBLE,
) -> Subscription
```
Register an event handler.

**Parameters:**
- `event_type` (`type[Event]`): The event type to listen for
- `handler` (`Callable[[Event], None]`): The handler function
- `phase` (`Phase`): Propagation phase (default: BUBBLE)

**Returns:** `Subscription` - Handle to remove the handler

#### `once`
```python
def once(
    self,
    event_type: type[Event],
    handler: Callable[[Event], None],
    phase: Phase = Phase.BUBBLE,
) -> Subscription
```
Register a one-time event handler (removed after first invocation).

**Parameters:**
- `event_type` (`type[Event]`): The event type to listen for
- `handler` (`Callable[[Event], None]`): The handler function
- `phase` (`Phase`): Propagation phase (default: BUBBLE)

**Returns:** `Subscription` - Handle to remove the handler

#### `emit`
```python
def emit(self, event: Event) -> None
```
Emit an event to local handlers (bubble phase).

**Parameters:**
- `event` (`Event`): The event to emit

---

## Class: `EventDispatcher`

Routes events through the widget tree.

### Methods

#### `dispatch`
```python
def dispatch(
    self,
    event: Event,
    target: Any,
    strategy: Strategy = Strategy.TUNNEL_THEN_BUBBLE,
) -> None
```
Dispatch an event to a target.

**Parameters:**
- `event` (`Event`): The event to dispatch
- `target` (`Any`): The target widget
- `strategy` (`Strategy`): Dispatch strategy

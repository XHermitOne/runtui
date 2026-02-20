# event_loop.py - Async Event Loop

Asyncio-based event loop for runtui applications.

---

## Class: `EventLoop`

The main event loop that reads input, dispatches events, and triggers paint/flush cycles.

### Constructor

```python
def __init__(self, backend: Backend) -> None
```

**Parameters:**
- `backend` (`Backend`): The terminal backend to use

### Properties

#### `dispatcher`
```python
@property
def dispatcher(self) -> EventDispatcher
```
Returns the event dispatcher instance.

#### `timers`
```python
@property
def timers(self) -> TimerManager
```
Returns the timer manager instance.

### Methods

#### `call_later`
```python
def call_later(
    self,
    delay: float,
    callback: Callable[[], None],
) -> TimerHandle
```

Schedule a callback after a delay.

**Parameters:**
- `delay` (`float`): Delay in seconds
- `callback` (`Callable[[], None]`): Function to call

**Returns:** `TimerHandle` - Handle to cancel

#### `set_interval`
```python
def set_interval(
    self,
    interval: float,
    callback: Callable[[], None],
) -> TimerHandle
```

Schedule a repeating callback.

**Parameters:**
- `interval` (`float`): Interval in seconds
- `callback` (`Callable[[], None]`): Function to call

**Returns:** `TimerHandle` - Handle to cancel

#### `call_soon`
```python
def call_soon(self, callback: Callable[[], None]) -> None
```

Schedule a callback to run on the next idle cycle.

**Parameters:**
- `callback` (`Callable[[], None]`): Function to call

#### `post_event`
```python
def post_event(self, event: Event) -> None
```

Queue an event to be dispatched on the next frame.

**Parameters:**
- `event` (`Event`): The event to post

#### `stop`
```python
def stop(self) -> None
```
Stop the event loop.

#### `run`
```python
async def run(self, app: Any) -> None
```

Run the main event loop.

**Parameters:**
- `app` (`Any`): The application instance

This is an async method that runs continuously until `stop()` is called.

### Loop Cycle

Each frame, the event loop:

1. Reads raw terminal input from the backend
2. Decodes input into events
3. Dispatches each event to the application
4. Processes timers
5. Processes idle callbacks
6. Paints and flushes the screen
7. Sleeps to maintain frame rate (default 60 FPS)
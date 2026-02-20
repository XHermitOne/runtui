# base.py - Backend Interface

Abstract backend interface for terminal I/O.

---

## Class: `Backend`

Abstract interface for terminal backends.

### Abstract Methods

#### `init`
```python
@abstractmethod
def init(self) -> None
```
Enter raw mode, alternate screen, and enable mouse tracking.

#### `shutdown`
```python
@abstractmethod
def shutdown(self) -> None
```
Restore terminal to original state.

#### `get_size`
```python
@abstractmethod
def get_size(self) -> tuple[int, int]
```
Get the terminal size.

**Returns:** `tuple[int, int]` - (columns, rows)

#### `read_input`
```python
@abstractmethod
def read_input(self) -> bytes
```
Read available raw bytes from terminal input (non-blocking).

**Returns:** `bytes` - Raw input bytes, or empty bytes if nothing available

#### `decode_input`
```python
@abstractmethod
def decode_input(self, raw: bytes) -> list[Event]
```
Parse raw bytes into Event objects.

**Parameters:**
- `raw` (`bytes`): Raw input bytes

**Returns:** `list[Event]` - Decoded events

#### `write`
```python
@abstractmethod
def write(self, data: str) -> None
```
Write string data (including escape sequences) to terminal.

**Parameters:**
- `data` (`str`): Data to write

#### `flush`
```python
@abstractmethod
def flush(self) -> None
```
Flush output buffer to terminal.

#### `set_cursor_position`
```python
@abstractmethod
def set_cursor_position(self, x: int, y: int) -> None
```
Move cursor to position (x, y) where (0, 0) is top-left.

**Parameters:**
- `x` (`int`): Column position
- `y` (`int`): Row position

#### `set_cursor_visible`
```python
@abstractmethod
def set_cursor_visible(self, visible: bool) -> None
```
Show or hide the hardware cursor.

**Parameters:**
- `visible` (`bool`): True to show, False to hide

#### `color_support`
```python
@abstractmethod
def color_support(self) -> ColorDepth
```
Detect the terminal's color depth capability.

**Returns:** `ColorDepth` - The detected color depth

### PTY Methods

#### `register_pty_fd`
```python
def register_pty_fd(self, fd: int, callback: Callable[[bytes], None]) -> None
```
Register a PTY master fd to be polled alongside stdin.

**Parameters:**
- `fd` (`int`): PTY master file descriptor
- `callback` (`Callable[[bytes], None]`): Callback for received data

#### `unregister_pty_fd`
```python
def unregister_pty_fd(self, fd: int) -> None
```
Remove a previously registered PTY fd.

**Parameters:**
- `fd` (`int`): PTY master file descriptor

### Terminal Escape Helpers

#### `enter_alternate_screen`
```python
def enter_alternate_screen(self) -> None
```
Switch to the alternate screen buffer.

#### `leave_alternate_screen`
```python
def leave_alternate_screen(self) -> None
```
Return to the main screen buffer.

#### `enable_mouse`
```python
def enable_mouse(self) -> None
```
Enable SGR any-event mouse tracking.

#### `disable_mouse`
```python
def disable_mouse(self) -> None
```
Disable mouse tracking.

#### `clear_screen`
```python
def clear_screen(self) -> None
```
Clear the screen.

#### `reset_attributes`
```python
def reset_attributes(self) -> None
```
Reset all text attributes to default.
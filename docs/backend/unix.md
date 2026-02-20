# unix.py - Unix Backend

Terminal backend for Linux and macOS using ANSI escape sequences.

---

## Class: `UnixBackend`

Terminal backend for Unix-like systems (Linux, macOS).

### Constructor

```python
def __init__(self) -> None
```

### Methods (Implementation of Backend)

#### `init`
```python
def init(self) -> None
```
- Saves original terminal settings (termios)
- Sets terminal to raw mode
- Enters alternate screen
- Hides cursor
- Enables mouse tracking
- Clears screen
- Installs SIGWINCH handler for resize events

#### `shutdown`
```python
def shutdown(self) -> None
```
- Disables mouse tracking
- Shows cursor
- Resets attributes
- Leaves alternate screen
- Restores original termios settings
- Restores SIGWINCH handler

#### `get_size`
```python
def get_size(self) -> tuple[int, int]
```
Uses `os.get_terminal_size()`. Returns (80, 24) on error.

#### `read_input`
```python
def read_input(self) -> bytes
```
Uses `select()` on stdin and any registered PTY fds to poll for input.

Also handles SIGWINCH resize events by synthesizing a marker.

#### `decode_input`
```python
def decode_input(self, raw: bytes) -> list[Event]
```
Parses ANSI escape sequences including:
- CSI sequences (arrow keys, function keys, etc.)
- SS3 sequences (F1-F4, Home, End)
- SGR mouse reports
- Control characters (Ctrl+letter)
- UTF-8 characters
- Alt+key combinations

#### `register_pty_fd` / `unregister_pty_fd`
```python
def register_pty_fd(self, fd: int, callback: Callable[[bytes], None]) -> None
def unregister_pty_fd(self, fd: int) -> None
```
Register PTY file descriptors for polling in the select() loop.

#### `write` / `flush`
```python
def write(self, data: str) -> None
def flush(self) -> None
```
Write to stdout with UTF-8 encoding.

#### `set_cursor_position`
```python
def set_cursor_position(self, x: int, y: int) -> None
```
Uses ANSI cursor position escape: `ESC[row;colH`

#### `set_cursor_visible`
```python
def set_cursor_visible(self, visible: bool) -> None
```
Uses DECTCEM cursor show/hide: `ESC[?25h` / `ESC[?25l`

#### `color_support`
```python
def color_support(self) -> ColorDepth
```
Detects color support by checking:
- `COLORTERM` environment variable
- `TERM` environment variable

Returns TRUE_COLOR, COLORS_256, or COLORS_16.

### Internal Methods

#### `_parse_escape`
```python
def _parse_escape(self, buf: bytes, start: int) -> tuple[int, Event | None]
```
Parse an escape sequence starting at buf[start].

#### `_parse_csi`
```python
def _parse_csi(self, buf: bytes, start: int) -> tuple[int, Event | None]
```
Parse CSI (Control Sequence Introducer) sequences.

#### `_parse_ss3`
```python
def _parse_ss3(self, buf: bytes, start: int) -> tuple[int, Event | None]
```
Parse SS3 sequences for function keys.

#### `_parse_sgr_mouse`
```python
def _parse_sgr_mouse(self, buf: bytes, start: int) -> tuple[int, Event | None]
```
Parse SGR mouse reports.

#### `_decode_control`
```python
def _decode_control(self, byte: int) -> Event | None
```
Decode control characters (0x00-0x1F).

#### `_decode_utf8`
```python
def _decode_utf8(self, buf: bytes, start: int) -> tuple[int, str]
```
Decode a single UTF-8 character.
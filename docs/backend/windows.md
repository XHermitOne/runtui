# windows.py - Windows Backend

Terminal backend for Windows using VT100 escape sequences via modern console APIs.

---

## Class: `WindowsBackend`

Terminal backend for Windows systems.

Uses VT100 escape sequences via Windows Terminal, ConEmu, or modern cmd.exe. Falls back gracefully for older terminals.

### Constructor

```python
def __init__(self) -> None
```

### Methods (Implementation of Backend)

#### `init`
```python
def init(self) -> None
```
- Uses Win32 Console API via ctypes
- Saves original console modes
- Enables VT (Virtual Terminal) processing
- Enables mouse and window input
- Sets UTF-8 code page (65001)
- Enters alternate screen
- Hides cursor
- Enables mouse tracking

Falls back gracefully if Win32 API is unavailable.

#### `shutdown`
```python
def shutdown(self) -> None
```
- Disables mouse tracking
- Shows cursor
- Resets attributes
- Leaves alternate screen
- Restores original console modes

#### `get_size`
```python
def get_size(self) -> tuple[int, int]
```
Uses `os.get_terminal_size()`. Returns (80, 24) on error.

#### `read_input`
```python
def read_input(self) -> bytes
```
Uses `msvcrt.kbhit()` and `msvcrt.getch()` for non-blocking input.

Falls back to `select.select()` if msvcrt is unavailable.

#### `decode_input`
```python
def decode_input(self, raw: bytes) -> list[Event]
```
Delegates to `UnixBackend.decode_input()` since Windows Terminal sends the same ANSI sequences as xterm.

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
- `WT_SESSION` (Windows Terminal session ID)
- `COLORTERM` environment variable
- `ConEmuANSI` environment variable

Returns TRUE_COLOR for Windows Terminal/ConEmu, COLORS_256 otherwise.
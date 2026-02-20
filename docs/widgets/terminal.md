# widgets/terminal.py - TerminalWidget

PTY-based terminal emulator widget with full VT100 support.

---

## Class: `TerminalWidget`

A widget that embeds a real terminal running in a PTY using the `pyte` library to parse VT100/xterm escape sequences.

### Features

- Interactive programs (vim, htop, bash) work correctly
- Full ANSI color support (16, 256, and 24-bit true color)
- Non-blocking I/O — PTY master fd is polled via backend's select()
- Scrollback history via pyte.HistoryScreen
- TIOCSWINSZ resize notification to child on widget resize
- Text selection with copy to clipboard
- Mouse scroll wheel support

### Constructor

```python
def __init__(
    self,
    shell: str = "",
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 80,
    height: int = 24,
) -> None
```

**Parameters:**
- `shell` (`str`): Shell to run (default: $SHELL or /bin/bash)
- `id` (`str | None`): Widget identifier
- `x` (`int`): X position
- `y` (`int`): Y position
- `width` (`int`): Initial width (default: 80)
- `height` (`int`): Initial height (default: 24)

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_running` | `bool` | Whether the terminal is running |

### Methods

#### `set_backend`
```python
def set_backend(self, backend: Backend) -> None
```
Set the backend for PTY fd registration.

**Parameters:**
- `backend` (`Backend`): The terminal backend

#### `start`
```python
def start(self, command: str = "") -> None
```
Start the terminal.

**Parameters:**
- `command` (`str`): If given, run this command; otherwise start shell

#### `stop`
```python
def stop(self) -> None
```
Stop the terminal and kill the child process.

#### `write_input`
```python
def write_input(self, text: str) -> None
```
Write text to the PTY as if the user typed it.

**Parameters:**
- `text` (`str`): Text to write

#### `write_output`
```python
def write_output(self, text: str) -> None
```
Feed text directly into the pyte screen (for programmatic use).

**Parameters:**
- `text` (`str`): Text to feed

#### `copy_selection`
```python
def copy_selection(self) -> str
```
Copy selected text to system clipboard.

**Returns:** `str` - The copied text

### Scrollback

The terminal maintains 2000 lines of scrollback history. Use:
- Scroll wheel to navigate history
- Scrollbar on the right edge for navigation
- Any keyboard input snaps back to live view

### Text Selection

- Left-click and drag to select text
- Selection is automatically copied to clipboard on release
- Right-click to copy current selection

### Default Colors

| Element | Color |
|---------|-------|
| Background | Dark gray (30, 30, 30) |
| Foreground | Light gray (200, 200, 200) |
| Scrollbar track | Dark gray (80, 80, 80) |
| Scrollbar thumb | Medium gray (160, 160, 160) |

### Usage

```python
from runtui.widgets.terminal import TerminalWidget

terminal = TerminalWidget(
    shell="/bin/bash",
    width=80,
    height=24,
)

# Set backend before starting
terminal.set_backend(app._backend)

# Start with shell or command
terminal.start()  # Shell
# or
terminal.start(command="vim myfile.txt")  # Specific command

# Add to container
container.add_child(terminal)

# Clean up
terminal.stop()
```

### Requirements

Requires `pyte` library for terminal emulation:

```bash
pip install pyte
```

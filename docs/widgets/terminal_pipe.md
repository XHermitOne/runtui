# widgets/terminal_pipe.py - PipeTerminalWidget

Terminal widget with pipe input.

---

## Class: `PipeTerminalWidget`

A terminal widget that receives input from a pipe.

### Constructor

```python
def __init__(
    self,
    command: list[str] | None = None,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 80,
    height: int = 24,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> None
```

Similar to `TerminalWidget` but designed for receiving piped input rather than interactive use.

### Methods

#### `write`
```python
def write(self, data: bytes) -> None
```
Write data to the terminal's stdin.

#### `send_keys`
```python
def send_keys(self, key_event: KeyEvent) -> None
```
Send a keyboard event to the terminal.

### Usage

Used for running commands and displaying their output non-interactively.
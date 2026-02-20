# pty_process.py - PTY Process Management

PTY (pseudo-terminal) process lifecycle manager for running child processes with a real terminal.

---

## Class: `PtyProcess`

Manages a child process running inside a PTY. Used by terminal widgets to embed shell sessions.

### Constructor

```python
def __init__(self) -> None
```

### Properties

#### `master_fd`
```python
@property
def master_fd(self) -> int
```
Returns the PTY master file descriptor.

#### `child_pid`
```python
@property
def child_pid(self) -> int
```
Returns the child process PID.

#### `alive`
```python
@property
def alive(self) -> bool
```
Returns `True` if the child process is still running.

### Methods

#### `spawn`
```python
def spawn(
    self,
    argv: list[str],
    rows: int = 24,
    cols: int = 80,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> None
```

Fork a child process with a PTY.

**Parameters:**
- `argv` (`list[str]`): Command and arguments, e.g., `["/bin/bash"]`
- `rows` (`int`): Initial terminal rows (default: 24)
- `cols` (`int`): Initial terminal columns (default: 80)
- `cwd` (`str | None`): Working directory for the child
- `env` (`dict[str, str] | None`): Environment variables (default: inherit from parent)

#### `read`
```python
def read(self, size: int = 65536) -> bytes
```

Read available data from the PTY master (non-blocking).

**Parameters:**
- `size` (`int`): Maximum bytes to read

**Returns:** `bytes` - Data read, or empty bytes if nothing available

**Raises:** `EOFError` if the child has exited

#### `write`
```python
def write(self, data: bytes) -> None
```

Write data to the PTY master (sends to child's stdin).

**Parameters:**
- `data` (`bytes`): Data to write

#### `resize`
```python
def resize(self, rows: int, cols: int) -> None
```

Notify the child of a terminal size change via TIOCSWINSZ.

**Parameters:**
- `rows` (`int`): New row count
- `cols` (`int`): New column count

#### `terminate`
```python
def terminate(self) -> int | None
```

Terminate the child process and clean up.

Sends SIGHUP first, then SIGKILL if still alive.

**Returns:** `int | None` - Exit status or None

#### `poll`
```python
def poll(self) -> int | None
```

Check if child is still running.

**Returns:** `int | None` - Exit code if terminated, None if still running
# rendering/screen.py - Screen Manager

Double buffering and diff-based terminal output.

---

## Class: `Screen`

Manages double-buffered rendering with diff-based terminal output.

### Constructor

```python
def __init__(self, backend: Backend) -> None
```

**Parameters:**
- `backend` (`Backend`): The terminal backend

### Properties

#### `width`
```python
@property
def width(self) -> int
```
Returns the screen width in columns.

#### `height`
```python
@property
def height(self) -> int
```
Returns the screen height in rows.

#### `front`
```python
front: CellBuffer
```
The front buffer (what's currently on screen).

#### `back`
```python
back: CellBuffer
```
The back buffer (what's being rendered).

### Methods

#### `resize`
```python
def resize(self, width: int, height: int) -> None
```
Resize the screen buffers.

**Parameters:**
- `width` (`int`): New width in columns
- `height` (`int`): New height in rows

#### `clear`
```python
def clear(
    self,
    fg: Color = Color.DEFAULT,
    bg: Color = Color.DEFAULT,
) -> None
```
Clear the back buffer.

**Parameters:**
- `fg` (`Color`): Foreground color
- `bg` (`Color`): Background color

#### `flush`
```python
def flush(self) -> None
```
Diff back buffer vs front buffer and write only changed cells to terminal.

This method:
1. Compares each cell in back vs front
2. Only outputs cells that have changed
3. Handles wide character continuation cells
4. Optimizes cursor movement for contiguous changes
5. Batches attribute/color changes
6. Copies back buffer to front buffer after flush

#### `force_full_redraw`
```python
def force_full_redraw(self) -> None
```
Mark all front buffer cells as different to force a full redraw on the next flush.

Call this after theme changes or other events that require a full repaint.

### Double Buffering

The screen uses two buffers:

- **Front buffer**: Represents what's currently displayed
- **Back buffer**: Where widgets paint during the frame

The `flush()` method compares the two and only sends changes to the terminal, minimizing output and improving performance.

### Wide Character Handling

The screen properly handles wide characters (emoji, CJK):
- Continuation cells are skipped during output
- Terminal cursor advances 2 positions after wide chars
- Ghost half-cells from replaced wide chars are detected and cleared

### Optimization Strategies

1. **Skip unchanged cells**: Only output cells that differ between front and back
2. **Contiguous writes**: Avoid cursor positioning when writing adjacent cells
3. **Batch attributes**: Only emit ANSI sequences when colors/attrs change
4. **Wide char tracking**: Account for terminal cursor behavior with wide chars

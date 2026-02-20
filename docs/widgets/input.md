# widgets/input.py - TextInput Widget

Single-line text input field.

---

## Class: `TextInput`

Single-line text input field with cursor, selection, and scrolling.

### Constructor

```python
def __init__(
    self,
    text: str = "",
    placeholder: str = "",
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 20,
    height: int = 1,
    max_length: int = 0,
    on_change: Callable[[str], None] | None = None,
    on_submit: Callable[[str], None] | None = None,
) -> None
```

**Parameters:**
- `text` (`str`): Initial text value
- `placeholder` (`str`): Placeholder text when empty
- `id` (`str | None`): Widget identifier
- `x` (`int`): X position
- `y` (`int`): Y position
- `width` (`int`): Width
- `height` (`int`): Height
- `max_length` (`int`): Maximum character length (0 = unlimited)
- `on_change` (`Callable[[str], None] | None`): Callback when text changes
- `on_submit` (`Callable[[str], None] | None`): Callback when Enter is pressed

### Properties

#### `text`
```python
@property
def text(self) -> str
```
Get the current text value.

```python
@text.setter
def text(self, value: str) -> None
```
Set the text value.

#### `cursor_pos`
```python
@property
def cursor_pos(self) -> int
```
Get the cursor position (character index).

### Key Bindings

| Key | Action |
|-----|--------|
| Left/Right arrow | Move cursor |
| Home/End | Move to start/end |
| Backspace | Delete character before cursor |
| Delete | Delete character at cursor |
| Enter | Submit (call on_submit) |
| Ctrl+A | Select all |

### Mouse Interaction

- Click to position cursor
- Click to focus

### Theme Colors

| Slot | Description |
|------|-------------|
| `input.fg` | Normal text color |
| `input.bg` | Normal background |
| `input.focused.fg` | Focused text color |
| `input.focused.bg` | Focused background |
| `input.placeholder` | Placeholder text color |
| `input.selection.fg` | Selection text color |
| `input.selection.bg` | Selection background |
| `input.cursor` | Cursor color |
| `input.cursor.bg` | Cursor background |

### Usage

```python
def on_text_change(text):
    print(f"Text: {text}")

def on_submit(text):
    print(f"Submitted: {text}")

input = TextInput(
    placeholder="Enter your name...",
    on_change=on_text_change,
    on_submit=on_submit,
)
```
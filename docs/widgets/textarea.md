# widgets/textarea.py - TextArea Widget

Multi-line text editing area with scrolling, selection, search, and syntax highlighting.

---

## Class: `TextArea`

Multi-line text editing area with scrollbars, selection, undo/redo support, search/replace, and optional syntax highlighting.

### Constructor

```python
def __init__(
    self,
    text: str = "",
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 40,
    height: int = 10,
    word_wrap: bool = False,
    readonly: bool = False,
    on_change: Callable[[str], None] | None = None,
) -> None
```

**Parameters:**
- `text` (`str`): Initial text content
- `id` (`str | None`): Widget identifier
- `x` (`int`): X position
- `y` (`int`): Y position
- `width` (`int`): Width in columns
- `height` (`int`): Height in rows
- `word_wrap` (`bool`): Enable word wrap (not yet implemented)
- `readonly` (`bool`): Prevent editing
- `on_change` (`Callable[[str], None]`): Callback when text changes

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `text` | `str` | Full text content (get/set) |
| `line_count` | `int` | Number of lines |
| `word_wrap` | `bool` | Word wrap mode |
| `readonly` | `bool` | Read-only mode |

### Methods

#### `set_syntax`
```python
def set_syntax(self, highlighter: SyntaxHighlighter | None) -> None
```
Set a SyntaxHighlighter for code highlighting.

**Parameters:**
- `highlighter` (`SyntaxHighlighter | None`): The highlighter or None to disable

### Key Bindings

| Key | Action |
|-----|--------|
| Arrow keys | Move cursor |
| Home/End | Start/end of line |
| Page Up/Down | Scroll by page |
| Enter | Insert newline |
| Backspace/Delete | Delete character/line |
| Tab | Insert 4 spaces |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+F | Open search bar |
| Ctrl+H | Open search/replace bar |
| Ctrl+A | Select all |
| Ctrl+C | Copy selection |
| Ctrl+X | Cut selection |
| Ctrl+V | Paste |
| F3 / Ctrl+G | Next search match |
| Shift+F3 | Previous search match |
| Escape | Close search bar |

### Mouse Support

- Click to position cursor
- Shift+Click to extend selection
- Drag to select text
- Scroll wheel to scroll content
- Click on scrollbars to navigate

### Scrollbars

The TextArea displays both vertical and horizontal scrollbars when content exceeds the visible area:
- Vertical scrollbar on the right edge
- Horizontal scrollbar at the bottom
- Corner character at scrollbar intersection

### Search/Replace Bar

When activated (Ctrl+F or Ctrl+H), a two-row bar appears at the bottom:
- Row 1: Search field with match count
- Row 2: Replace field with [Repl] and [All] buttons

Features:
- Real-time match highlighting
- Navigate between matches with Enter/F3
- Replace current or all matches

### Syntax Highlighting

The TextArea supports syntax highlighting via `SyntaxHighlighter` instances:

```python
from runtui.widgets.textarea import TextArea
from runtui.widgets.syntax import SyntaxHighlighter

textarea = TextArea()
highlighter = SyntaxHighlighter.for_extension(".py")
textarea.set_syntax(highlighter)
```

### Selection

- Click and drag to select
- Shift+arrow keys to extend selection
- Ctrl+A to select all
- Selection is highlighted with theme colors
- Clipboard operations work on selection

### Theme Colors

| Slot | Description |
|------|-------------|
| `input.fg` | Normal text color |
| `input.bg` | Normal background |
| `input.focused.fg` | Focused text color |
| `input.focused.bg` | Focused background |
| `input.selection.fg` | Selection text color |
| `input.selection.bg` | Selection background |
| `scrollbar.track` | Scrollbar track color |
| `scrollbar.thumb` | Scrollbar thumb color |
| `scrollbar.arrow` | Scrollbar arrow color |

### Usage

```python
from runtui import TextArea

# Basic usage
textarea = TextArea(
    text="Hello\nWorld",
    width=60,
    height=15,
    on_change=lambda text: print(f"Changed: {len(text)} chars"),
)

# Read-only code display
code = TextArea(text=source_code, readonly=True)
code.set_syntax(SyntaxHighlighter.for_extension(".py"))

# With initial content
textarea = TextArea()
textarea.text = "Multi-line\ncontent\nhere"
```

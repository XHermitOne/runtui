# widgets/syntax.py - Syntax Highlighter

Regex-based syntax highlighting for TextArea widget.

---

## Class: `SyntaxHighlighter`

Base class for per-language highlighters.

### Methods

#### `highlight_line`
```python
def highlight_line(self, line: str, line_index: int) -> list[Color | None]
```

Return a list of `Color | None`, one per character in the line.

**Parameters:**
- `line` (`str`): The line of text to highlight
- `line_index` (`int`): The line number (for multi-line context)

**Returns:** `list[Color | None]` - Per-character colors (`None` means default fg)

### Factory Methods

#### `register`
```python
@classmethod
def register(cls, *extensions: str)
```
Decorator to register a highlighter for file extensions.

#### `for_extension`
```python
@classmethod
def for_extension(cls, ext: str) -> SyntaxHighlighter | None
```
Return a highlighter instance for the given extension, or `None`.

**Parameters:**
- `ext` (`str`): File extension including dot (e.g., `.py`)

**Returns:** `SyntaxHighlighter | None` - The highlighter or `None` if not found

### Color Palette

| Constant | Color | Use |
|----------|-------|-----|
| `C_KEYWORD` | Purple | Keywords |
| `C_BUILTIN` | Cyan | Built-in functions/types |
| `C_STRING` | Orange-brown | String literals |
| `C_COMMENT` | Green | Comments |
| `C_NUMBER` | Light green | Numeric literals |
| `C_DECORATOR` | Gold | Decorators/annotations |
| `C_TAG` | Blue | HTML/XML tags |
| `C_ATTR` | Light blue | HTML attributes |
| `C_FUNC` | Pale yellow | Function names |
| `C_CONST` | Teal | Constants (True, False, None) |

### Supported Languages

| Language | Extensions | Highlighter Class |
|----------|------------|-------------------|
| Python | `.py` | `PythonHighlighter` |
| Shell/Bash | `.sh`, `.bash`, `.zsh` | `ShellHighlighter` |
| HTML | `.html`, `.htm` | `HtmlHighlighter` |
| JavaScript | `.js` | `JavaScriptHighlighter` |
| TypeScript | `.ts`, `.tsx` | `TypeScriptHighlighter` |
| C/C++ | `.c`, `.h`, `.cpp`, `.hpp`, `.cc`, `.cxx` | `CppHighlighter` |
| Java | `.java` | `JavaHighlighter` |
| C# | `.cs` | `CSharpHighlighter` |
| Go | `.go` | `GoHighlighter` |
| R | `.r`, `.R` | `RHighlighter` |
| SQL | `.sql` | `SqlHighlighter` |

### Usage

```python
from runtui.widgets.syntax import SyntaxHighlighter
from runtui.widgets.textarea import TextArea

# Get highlighter for a file extension
highlighter = SyntaxHighlighter.for_extension(".py")

# Apply to TextArea
textarea = TextArea()
textarea.set_syntax(highlighter)

# The TextArea will now highlight code as it's typed
```

### Multi-line Support

Some highlighters (Python, C-style languages) track state across lines:
- Python: Tracks triple-quoted strings
- C/C++/Java/C#/Go/TypeScript: Tracks block comments (`/* ... */`)

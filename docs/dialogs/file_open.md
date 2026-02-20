# dialogs/file_open.py - Open File Dialog

File open selection dialog.

---

## Class: `OpenFileDialog`

A dialog for selecting a file to open.

### Constructor

```python
def __init__(
    self,
    initial_dir: str = ".",
    title: str = "Open File",
    filters: list[str] | None = None,
) -> None
```

**Parameters:**
- `initial_dir` (`str`): Starting directory
- `title` (`str`): Dialog title
- `filters` (`list[str] | None`): File type filters, e.g., `["*.txt", "*.py"]`

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `selected_path` | `str \| None` | Path to selected file |
| `selected_file` | `str` | Filename only |

### Methods

#### `refresh`
```python
def refresh(self) -> None
```
Refresh the file list.

### Usage

```python
dialog = OpenFileDialog(initial_dir=".", filters=["*.py", "*.txt"])
# After dialog closes:
if dialog.selected_path:
    with open(dialog.selected_path) as f:
        content = f.read()
```
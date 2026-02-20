# dialogs/file_save.py - Save File Dialog

File save selection dialog.

---

## Class: `SaveFileDialog`

A dialog for selecting where to save a file.

### Constructor

```python
def __init__(
    self,
    initial_dir: str = ".",
    initial_name: str = "",
    title: str = "Save File",
    filters: list[str] | None = None,
) -> None
```

**Parameters:**
- `initial_dir` (`str`): Starting directory
- `initial_name` (`str`): Default filename
- `title` (`str`): Dialog title
- `filters` (`list[str] | None`): File type filters

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `selected_path` | `str \| None` | Full path for saving |
| `selected_file` | `str` | Filename only |

### Methods

#### `refresh`
```python
def refresh(self) -> None
```
Refresh the file list.

### Usage

```python
dialog = SaveFileDialog(
    initial_dir=".",
    initial_name="untitled.txt",
    filters=["*.txt"],
)
# After dialog closes:
if dialog.selected_path:
    with open(dialog.selected_path, "w") as f:
        f.write(content)
```
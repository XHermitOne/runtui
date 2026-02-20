# dialogs/form.py - Form Dialog

Form input dialog with multiple fields.

---

## Class: `FormDialog`

A dialog with labeled input fields.

### Constructor

```python
def __init__(
    self,
    title: str = "Form",
    fields: list[tuple[str, str, str]] | None = None,
) -> None
```

**Parameters:**
- `title` (`str`): Dialog title
- `fields` (`list[tuple[str, str, str]]`): List of (label, key, default_value) tuples

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `values` | `dict[str, str]` | Field values by key |

### Methods

#### `get_value`
```python
def get_value(self, key: str) -> str
```
Get a field value by key.

#### `set_value`
```python
def set_value(self, key: str, value: str) -> None
```
Set a field value.

### Usage

```python
dialog = FormDialog(
    title="Login",
    fields=[
        ("Username:", "username", ""),
        ("Password:", "password", ""),
    ],
)
# After dialog closes:
if dialog.result == "ok":
    username = dialog.get_value("username")
    password = dialog.get_value("password")
```
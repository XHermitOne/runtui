# widgets/password.py - PasswordInput Widget

Password input that masks characters.

---

## Class: `PasswordInput`

Password input field that masks characters with a mask character. Inherits from `TextInput`.

### Constructor

```python
def __init__(
    self,
    text: str = "",
    placeholder: str = "Password",
    mask_char: str = "●",
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
- `placeholder` (`str`): Placeholder text (default: "Password")
- `mask_char` (`str`): Character to display instead of actual text (default: "●")
- Other parameters same as `TextInput`

### Methods

#### `paint`
```python
def paint(self, painter: Painter) -> None
```
Draw the masked text and cursor.

### Usage

```python
password = PasswordInput(placeholder="Enter password...")
```
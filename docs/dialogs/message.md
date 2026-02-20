# dialogs/message.py - MessageBox Dialog

Simple message display dialog.

---

## Class: `MessageBox`

A dialog that displays a message with OK/Cancel buttons.

### Constructor

```python
def __init__(
    self,
    message: str = "",
    title: str = "Message",
    buttons: str = "ok",
) -> None
```

**Parameters:**
- `message` (`str`): The message to display
- `title` (`str`): Dialog title
- `buttons` (`str`): Button configuration:
  - `"ok"` - Just an OK button
  - `"okcancel"` - OK and Cancel buttons
  - `"yesno"` - Yes and No buttons

### Properties

#### `result`
Returns the button that was clicked: `"ok"`, `"cancel"`, `"yes"`, or `"no"`.

### Static Factory Methods

#### `info`
```python
@staticmethod
def info(message: str, title: str = "Information") -> MessageBox
```
Create an information message box.

#### `warning`
```python
@staticmethod
def warning(message: str, title: str = "Warning") -> MessageBox
```
Create a warning message box.

#### `error`
```python
@staticmethod
def error(message: str, title: str = "Error") -> MessageBox
```
Create an error message box.

#### `confirm`
```python
@staticmethod
def confirm(message: str, title: str = "Confirm") -> MessageBox
```
Create a confirmation dialog (Yes/No buttons).
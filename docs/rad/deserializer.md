# rad/deserializer.py - Widget Deserializer

Deserialize JSON designs into live widget trees.

---

## Functions

### `deserialize_widget`
```python
def deserialize_widget(
    widget_data: dict,
    radio_groups: dict[str, Any] | None = None
) -> Any
```

Create a live runtui widget from a JSON widget descriptor.

**Parameters:**
- `widget_data` (`dict`): Widget descriptor with type, props, id, events
- `radio_groups` (`dict[str, Any] | None`): Shared RadioGroup instances

**Returns:** The widget instance

### `load_menu_data`
```python
def load_menu_data(data: dict)
```

Extract and reconstruct MenuDesignData from a design dict.

**Parameters:**
- `data` (`dict`): The full design dictionary

**Returns:** `MenuDesignData | None` - Menu data or `None` if no menus

### `load_json`
```python
def load_json(path: str) -> dict
```

Load a JSON design file.

**Parameters:**
- `path` (`str`): Path to JSON file

**Returns:** `dict` - The parsed JSON data

### `load_design`
```python
def load_design(data: dict) -> list[dict]
```

Parse a design dict and return window descriptors.

Each window descriptor has:
- `"window"`: dict with id, title, x, y, width, height
- `"widgets"`: list of (widget, widget_data) tuples

**Parameters:**
- `data` (`dict`): The full design dictionary

**Returns:** `list[dict]` - List of window descriptors

## Supported Widget Types

| Type Name | Class | Module |
|-----------|-------|--------|
| `Label` | `Label` | `runtui.widgets.label` |
| `Button` | `Button` | `runtui.widgets.button` |
| `TextInput` | `TextInput` | `runtui.widgets.input` |
| `PasswordInput` | `PasswordInput` | `runtui.widgets.password` |
| `Checkbox` | `Checkbox` | `runtui.widgets.checkbox` |
| `RadioButton` | `RadioButton` | `runtui.widgets.radio` |
| `TextArea` | `TextArea` | `runtui.widgets.textarea` |
| `ListBox` | `ListBox` | `runtui.widgets.listbox` |
| `DropDownList` | `DropDownList` | `runtui.widgets.dropdown` |
| `ProgressBar` | `ProgressBar` | `runtui.widgets.progressbar` |
| `Calendar` | `Calendar` | `runtui.widgets.calendar` |
| `VScrollbar` | `VScrollbar` | `runtui.widgets.scrollbar` |
| `HScrollbar` | `HScrollbar` | `runtui.widgets.scrollbar` |
| `ImageWidget` | `ImageWidget` | `runtui.widgets.image` |
| `StaticImage` | `StaticImage` | `runtui.widgets.static_image` |

## Type Coercion

The deserializer automatically coerces JSON values to expected Python types:

| JSON Type | Python Type |
|-----------|-------------|
| `"int"` | `int` |
| `"float"` | `float` |
| `"bool"` | `bool` (handles string "true"/"false") |
| `"str"` | `str` |
| `"list[str]"` | `list[str]` |

## Usage

```python
from runtui.rad.deserializer import load_json, load_design, deserialize_widget

# Load full design
data = load_json("my_app.json")
windows = load_design(data)

for win_desc in windows:
    window_info = win_desc["window"]
    for widget, widget_data in win_desc["widgets"]:
        print(f"Created {widget_data['type']}: {widget}")

# Or deserialize a single widget
widget_data = {
    "type": "Button",
    "id": "btn1",
    "props": {"text": "Click Me"},
    "events": {"on_click": "handle_click"}
}
button = deserialize_widget(widget_data)
```

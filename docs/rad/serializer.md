# rad/serializer.py - Widget Serializer

Serialize design surfaces to JSON format.

---

## Functions

### `widget_to_dict`
```python
def widget_to_dict(
    widget: Any,
    type_name: str,
    widget_id: str,
    events: dict[str, str],
    original_pos: tuple[int, int, int, int] | None = None,
) -> dict
```

Convert a single design widget to a JSON-serializable dict.

**Parameters:**
- `widget` (`Any`): The live widget instance
- `type_name` (`str`): Widget type name
- `widget_id` (`str`): Widget identifier
- `events` (`dict[str, str]`): Event handler mappings
- `original_pos` (`tuple[int, int, int, int] | None`): (x, y, width, height) from layout

**Returns:** `dict` - JSON-serializable widget descriptor

### `serialize_design`
```python
def serialize_design(
    surface: DesignSurface,
    app_settings: dict | None = None,
    menu_data: Any = None,
) -> dict
```

Convert a DesignSurface's full widget tree to a JSON-serializable dict.

**Parameters:**
- `surface` (`DesignSurface`): The design surface
- `app_settings` (`dict | None`): App configuration (theme, title, window settings)
- `menu_data` (`Any`): Menu design data

**Returns:** `dict` - Complete design dictionary

### `save_json`
```python
def save_json(data: dict, path: str) -> None
```

Write a design dict to a JSON file.

**Parameters:**
- `data` (`dict`): The design dictionary
- `path` (`str`): File path to write

## Output Format

```json
{
  "$schema": "runtui-rad-v1",
  "app": {
    "theme": "light",
    "title": "My Application"
  },
  "windows": [{
    "id": "main_window",
    "title": "Main Window",
    "x": 5,
    "y": 2,
    "width": 40,
    "height": 20,
    "widgets": [
      {
        "type": "Label",
        "id": "lbl1",
        "props": {
          "text": "Hello",
          "x": 2,
          "y": 1
        }
      },
      {
        "type": "Button",
        "id": "btn1",
        "props": {
          "text": "Click",
          "x": 2,
          "y": 3
        },
        "events": {
          "on_click": "handle_click"
        }
      }
    ]
  }],
  "radio_groups": ["group1"],
  "menus": [...]
}
```

## Serialized Properties

The serializer captures:
- Widget type and ID
- Position (x, y) from AbsoluteLayout cache
- Size (width, height)
- Content properties (text, label, items, etc.)
- State properties (checked, selected, value)
- Event handler names

Default values are omitted to keep files small.

## Usage

```python
from runtui.rad.serializer import serialize_design, save_json

# Serialize design
data = serialize_design(
    surface,
    app_settings={
        "theme": "light",
        "title": "My App",
        "window_title": "Main Window",
    },
    menu_data=menu_design,
)

# Save to file
save_json(data, "my_app.json")
```

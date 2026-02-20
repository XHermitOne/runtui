# rad/schema.py - Widget Schema

Widget metadata registry for the RAD designer.

---

## Class: `PropertyDef`

Definition of a single editable widget property.

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Property name |
| `prop_type` | `str` | required | Type: "str", "int", "float", "bool", "list[str]" |
| `default` | `Any` | `None` | Default value |
| `category` | `str` | `"layout"` | Category: "layout", "content", "behavior", "appearance" |

---

## Class: `WidgetTypeDef`

Definition of a widget type for the designer toolbox.

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Widget type name |
| `class_name` | `str` | required | Python class name |
| `icon` | `str` | required | Display icon |
| `properties` | `list[PropertyDef]` | `[]` | Editable properties |
| `default_width` | `int` | `20` | Default width |
| `default_height` | `int` | `1` | Default height |
| `events` | `list[str]` | `[]` | Supported event names |

---

## Common Properties

All widgets share these layout properties:

| Property | Type | Default |
|----------|------|---------|
| `x` | `int` | `0` |
| `y` | `int` | `0` |
| `width` | `int` | `0` |
| `height` | `int` | `1` |

---

## Registered Widgets

### Display Widgets

| Type | Icon | Default Size | Properties |
|------|------|--------------|------------|
| `Label` | `Aa` | 12x1 | text, align, bold |
| `ProgressBar` | `██` | 20x1 | value, max_value, show_percentage |

### Input Widgets

| Type | Icon | Default Size | Properties | Events |
|------|------|--------------|------------|--------|
| `Button` | `[B]` | 12x1 | text | on_click |
| `TextInput` | `[_]` | 22x1 | text, placeholder, max_length | on_change, on_submit |
| `PasswordInput` | `[*]` | 22x1 | text, placeholder, mask_char, max_length | on_change, on_submit |
| `Checkbox` | `[✓]` | 16x1 | label, checked | on_change |
| `RadioButton` | `(*)` | 16x1 | label, value, selected, group | - |
| `TextArea` | `≡T` | 30x8 | text, word_wrap, readonly | on_change |

### Selection Widgets

| Type | Icon | Default Size | Properties | Events |
|------|------|--------------|------------|--------|
| `ListBox` | `▤L` | 22x8 | items | on_select, on_activate |
| `DropDownList` | `▼D` | 22x1 | items, selected_index | on_change |
| `Calendar` | `📅` | 24x10 | - | on_select |

### Scrollbar Widgets

| Type | Icon | Default Size | Properties | Events |
|------|------|--------------|------------|--------|
| `VScrollbar` | `▐S` | 1x10 | total, visible_amount, value | on_change |
| `HScrollbar` | `▬S` | 20x1 | total, visible_amount, value | on_change |

### Media Widgets

| Type | Icon | Default Size | Properties |
|------|------|--------------|------------|
| `StaticImage` | `🖼` | 40x12 | filepath |

---

## Functions

### `get_widget_types`
```python
def get_widget_types() -> list[str]
```
Return list of all registered widget type names.

### `get_typedef`
```python
def get_typedef(type_name: str) -> WidgetTypeDef | None
```
Look up a widget type definition.

### `get_constructor_params`
```python
def get_constructor_params(type_name: str) -> list[str]
```
Return property names that map to constructor kwargs.

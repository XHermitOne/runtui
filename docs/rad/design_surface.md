# rad/design_surface.py - Design Surface

Visual design surface for widget placement and editing.

---

## Class: `DesignWidgetInfo`

Metadata about a widget placed on the design surface.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `widget` | `Widget` | The live widget instance |
| `widget_type` | `str` | Type name (e.g., "Button") |
| `widget_id` | `str` | Widget identifier |
| `events` | `dict[str, str]` | Event handler mappings |

---

## Class: `DesignSurface`

A container that intercepts mouse events for design-mode editing.

Widgets placed here are selectable and draggable but do NOT respond to their normal behavior (clicks, key input, etc.).

Uses TUNNEL-phase event interception so no existing widget code needs to be modified.

### Constructor

```python
def __init__(self) -> None
```

Creates a design surface with AbsoluteLayout.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `selected` | `DesignWidgetInfo \| None` | Currently selected widget |
| `active_tool` | `str \| None` | Active tool for placement |

### Callbacks

| Callback | Signature | Description |
|----------|-----------|-------------|
| `on_selection_changed` | `Callable[[DesignWidgetInfo \| None], None]` | Selection change callback |
| `on_widget_moved` | `Callable[[DesignWidgetInfo], None]` | Widget move callback |

### Methods

#### `add_design_widget`
```python
def add_design_widget(
    self,
    widget_type: str,
    rel_x: int,
    rel_y: int,
) -> DesignWidgetInfo | None
```

Create and place a new widget at the given position.

**Parameters:**
- `widget_type` (`str`): Type of widget to create
- `rel_x` (`int`): X position relative to surface
- `rel_y` (`int`): Y position relative to surface

**Returns:** `DesignWidgetInfo | None` - The created widget info

#### `remove_selected`
```python
def remove_selected(self) -> None
```
Remove the currently selected widget.

#### `duplicate_selected`
```python
def duplicate_selected(self) -> DesignWidgetInfo | None
```

Clone the selected widget at a small offset.

**Returns:** `DesignWidgetInfo | None` - The new widget info

#### `select_widget`
```python
def select_widget(self, info: DesignWidgetInfo | None) -> None
```
Set the selected widget.

#### `deselect`
```python
def deselect(self) -> None
```
Clear selection.

#### `get_all_widgets`
```python
def get_all_widgets(self) -> list[DesignWidgetInfo]
```
Return all design widgets on the surface.

#### `clear_all`
```python
def clear_all(self) -> None
```
Remove all design widgets from the surface.

#### `update_widget_position`
```python
def update_widget_position(
    self,
    info: DesignWidgetInfo,
    new_x: int,
    new_y: int,
) -> None
```
Update a widget's position in the layout.

#### `update_widget_size`
```python
def update_widget_size(
    self,
    info: DesignWidgetInfo,
    new_w: int,
    new_h: int,
) -> None
```
Update a widget's size in the layout.

#### `find_info_by_widget`
```python
def find_info_by_widget(self, widget: Widget) -> DesignWidgetInfo | None
```
Find the DesignWidgetInfo for a given widget.

#### `paint`
```python
def paint(self, painter: Painter) -> None
```
Paint background with dot grid pattern.

#### `paint_selection_overlay`
```python
def paint_selection_overlay(self, painter: Painter) -> None
```
Paint selection highlight over the selected widget. Called by the RAD app after window content is painted.

### Auto-generated IDs

Widget IDs are auto-generated with prefixes:

| Widget Type | Prefix | Example |
|-------------|--------|---------|
| Label | `lbl` | lbl1, lbl2 |
| Button | `btn` | btn1, btn2 |
| TextInput | `inp` | inp1, inp2 |
| PasswordInput | `pwd` | pwd1 |
| Checkbox | `chk` | chk1 |
| RadioButton | `rad` | rad1 |
| TextArea | `txt` | txt1 |
| ListBox | `lst` | lst1 |
| DropDownList | `ddl` | ddl1 |
| ProgressBar | `prg` | prg1 |
| Calendar | `cal` | cal1 |
| VScrollbar | `vsb` | vsb1 |
| HScrollbar | `hsb` | hsb1 |
| ImageWidget | `img` | img1 |
| StaticImage | `simg` | simg1 |

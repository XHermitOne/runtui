# examples/rad_designer.py - RAD Designer

A Visual Basic / Delphi-style IDE running entirely in the terminal.

---

## Overview

The RAD (Rapid Application Development) Designer is a visual form designer for runtui applications. It allows you to:

- Design forms by placing widgets on a canvas
- Edit widget properties in a properties panel
- Save/load designs as JSON
- Export designs as runnable Python code
- Preview designs live
- Design menu bars

---

## Class: `PropertiesPanel`

Manages the properties window, showing editable fields for the selected widget.

### Constructor

```python
def __init__(self, window: Window, surface: DesignSurface) -> None
```

**Parameters:**
- `window` (`Window`): The properties window
- `surface` (`DesignSurface`): The design surface

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `_current` | `DesignWidgetInfo \| None` | Currently selected widget |
| `_editors` | `dict[str, TextInput]` | Property editor inputs |

### Methods

| Method | Description |
|--------|-------------|
| `show_properties` | Rebuild panel for selected widget |
| `refresh_position` | Update position fields after drag |
| `_read_prop` | Read a property value |
| `_on_id_changed` | Handle ID field change |
| `_on_prop_changed` | Handle property value change |
| `_on_event_changed` | Handle event handler name change |

### Property Editors

For each widget property, creates appropriate editors:
- **string**: Text input
- **int**: Text input (parsed as integer)
- **float**: Text input (parsed as float)
- **bool**: Text input (true/false)
- **list[str]**: Comma-separated input

### Layout

The panel shows:
1. Widget type header
2. ID field
3. Type-specific properties (x, y, width, height, text, etc.)
4. Events section (if widget has events)

---

## Class: `RADDesignerApp`

Visual RAD Designer for runtui applications.

### Constructor

```python
def __init__(self) -> None
```

Initializes with:
- `_current_file`: Currently open design file path
- `_design_theme`: Theme for preview ("light")
- `_design_title`: Application title
- `_menu_design_data`: Menu structure for design

### Methods

#### Setup Methods

| Method | Description |
|--------|-------------|
| `on_ready` | Initialize the designer |
| `_setup_menu` | Create menu bar |
| `_create_toolbox` | Create toolbox window |
| `_create_canvas` | Create design canvas window |
| `_create_properties` | Create properties window |

#### Paint Override

```python
def _paint(self) -> None
```

Override to paint selection highlight clipped to the canvas window.

#### Toolbox Callbacks

| Method | Description |
|--------|-------------|
| `_on_tool_activated` | Double-click tool to set as active |

#### Selection Callbacks

| Method | Description |
|--------|-------------|
| `_on_selection_changed` | Update properties panel |
| `_on_widget_moved` | Refresh position fields |

#### Settings

| Method | Description |
|--------|-------------|
| `_get_app_settings` | Get app config for serialization |

#### File Operations

| Method | Description |
|--------|-------------|
| `_new_design` | Clear design |
| `_open_design` | Open JSON design file |
| `_finish_open` | Load design into surface |
| `_save_design` | Save to current file |
| `_save_design_as` | Save with new name |
| `_finish_save` | Write JSON file |
| `_export_python` | Export as Python code |
| `_finish_export` | Write Python file |
| `_check_dialog_result` | Poll dialog for result |

#### Edit Operations

| Method | Description |
|--------|-------------|
| `_delete_widget` | Remove selected widget |
| `_duplicate_widget` | Duplicate selected widget |
| `_edit_menus` | Open menu editor |
| `_finish_edit_menus` | Store edited menu data |

#### Run / Preview

| Method | Description |
|--------|-------------|
| `_preview` | Preview design in live window |

#### Theme

| Method | Description |
|--------|-------------|
| `_set_design_theme` | Change design theme |

---

## Menu Structure

| Menu | Items |
|------|-------|
| File | New, Open..., Save, Save As..., Export Python..., Exit |
| Edit | Delete Widget, Duplicate, Edit Menus... |
| Run | Preview (F5) |
| Theme | Turbo Vision, Dark, Light, Nord, Solarized |
| Help | About |

---

## Window Layout

The designer uses a three-panel layout:

```
┌──────────┬──────────────────────────────┬────────────────┐
│ Toolbox  │       Form Designer          │   Properties   │
│          │                              │                │
│ 📦 Label │  [Design Canvas]             │  [widget_type] │
│ 🔘 Button│                              │  id: widget1   │
│ 📝 Input │                              │  text: ...     │
│ ...      │                              │  x: 10         │
│          │                              │  y: 5          │
│          │                              │  ...           │
└──────────┴──────────────────────────────┴────────────────┘
```

### Toolbox Window

- Lists all available widget types from `WIDGET_REGISTRY`
- Double-click to select a widget type
- Click on canvas to place the widget
- Non-closable, non-minimizable

### Canvas Window

- Visual design surface (`DesignSurface`)
- Click to select widgets
- Drag to move widgets
- Displays selection highlight
- Title shows current file or selected widget

### Properties Window

- Shows properties for selected widget
- Edit ID, position, size, and content
- Event handler name assignment
- Non-closable, non-minimizable

---

## Widget Workflow

1. **Select Tool**: Double-click a widget type in the toolbox
2. **Place Widget**: Click on the canvas to place
3. **Edit Properties**: Modify properties in the right panel
4. **Move/Resize**: Drag widgets to reposition
5. **Edit Menus**: Use Edit → Edit Menus... to design menu bars
6. **Save**: Save as JSON for later editing
7. **Export**: Generate standalone Python code
8. **Preview**: Press F5 to preview live

---

## Output Formats

### JSON Design File

```json
{
  "$schema": "runtui-rad-v1",
  "app": {
    "theme": "light",
    "title": "My Application",
    "window_width": 46,
    "window_height": 22
  },
  "windows": [{
    "id": "main_window",
    "title": "Main Window",
    "x": 5,
    "y": 2,
    "width": 46,
    "height": 22,
    "widgets": [
      {
        "type": "Label",
        "id": "label1",
        "props": {
          "text": "Hello, World!",
          "x": 10,
          "y": 5
        }
      }
    ]
  }],
  "radio_groups": [],
  "menus": [...]
}
```

### Generated Python

```python
#!/usr/bin/env python3
"""Generated by runtui RAD Designer — My Application."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtui import (
    App, Window, Label, ...
)
from runtui.widgets.container import Container
from runtui.layout.absolute import AbsoluteLayout


class MyAppApp(App):
    """Application: My Application."""

    def __init__(self) -> None:
        super().__init__(theme="light")

    def on_ready(self) -> None:
        self.main_window = Window(
            title="Main Window",
            x=5, y=2, width=46, height=22,
        )

        content = Container()
        content._layout_manager = AbsoluteLayout()

        self.label1 = Label(text="Hello, World!", x=10, y=5)
        content.add_child(self.label1)

        self.main_window.set_content(content)
        self.add_window(self.main_window)


if __name__ == "__main__":
    app = MyAppApp()
    app.run()
```

---

## Running the Designer

```bash
cd /path/to/tui2
python examples/rad_designer.py
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New design |
| Ctrl+O | Open design |
| Ctrl+S | Save design |
| Ctrl+Q | Exit |
| F5 | Preview design |
| Delete | Delete selected widget |

---

## Dependencies

Uses the `runtui.rad` module:
- `schema`: Widget type definitions
- `design_surface`: Design canvas
- `serializer`: Save to JSON
- `deserializer`: Load from JSON
- `codegen`: Generate Python code
- `runner`: Live preview
- `menu_editor`: Menu bar designer

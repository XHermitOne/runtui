# examples/demo_app.py - Widget Demo Application

A comprehensive demo application showcasing all runtui widgets.

---

## Overview

The `demo_app.py` example demonstrates the full range of runtui widgets and features in a single application. It serves as both a reference and a testbed for the framework's capabilities.

---

## Class: `DemoApp`

A showcase application for all runtui widgets.

### Constructor

```python
def __init__(self) -> None:
    super().__init__(theme="light")
```

Initializes the app with the light theme.

### Methods

#### `on_ready`
```python
def on_ready(self) -> None
```
Called when the app is ready. Sets up the menu bar and creates demo windows:
- Input Widgets window
- List Demo window
- Calendar window
- Text Editor window

#### `_setup_menu`
```python
def _setup_menu(self) -> None
```
Creates the application menu bar with File, Windows, Theme, and Help menus.

**Menu Structure:**

| Menu | Items |
|------|-------|
| File | New Window, Open..., Save As..., Exit |
| Windows | Cascade, Tile Horizontal, Tile Vertical |
| Theme | Turbo Vision, Dark, Light, Nord, Solarized |
| Help | About |

#### `_create_input_demo`
```python
def _create_input_demo(self) -> None
```
Creates a window demonstrating input widgets:

**Layout (using AbsoluteLayout):**

| Row | Widgets |
|-----|---------|
| 0 | Label "Name:" + TextInput |
| 2 | Label "Password:" + PasswordInput |
| 4 | Checkbox "Bold" + Checkbox "Italic" |
| 6-8 | RadioButtons in RadioGroup |
| 10 | Label "Color:" + DropDownList |
| 12 | Label "Progress:" + ProgressBar |
| 14 | Button "OK" + Button "Cancel" |

**Widgets demonstrated:**
- **TextInput**: Single-line text entry
- **PasswordInput**: Masked password entry
- **Checkbox**: Boolean toggles
- **RadioButton** with **RadioGroup**: Mutually exclusive selection
- **DropDownList**: Dropdown selection
- **ProgressBar**: Progress indicator (65%)
- **Button**: Clickable buttons

#### `_create_list_demo`
```python
def _create_list_demo(self) -> None
```
Creates a window demonstrating the ListBox widget with:
- 20 scrollable items with star/circle markers
- Label showing item count

#### `_create_calendar_demo`
```python
def _create_calendar_demo(self) -> None
```
Creates a window demonstrating the Calendar widget with:
- Today's date pre-selected
- Standard calendar navigation

#### `_create_editor_demo`
```python
def _create_editor_demo(self) -> None
```
Creates a window demonstrating the TextArea widget with:
- Multi-line text editing
- Sample text showcasing features
- Full navigation and editing support

**Sample text includes:**
```
# Welcome to runtui!

This is a multi-line text editor.
It supports:
  - Arrow key navigation
  - Backspace and Delete
  - Home/End/PgUp/PgDn
  - Undo (Ctrl+Z)
  - Mouse click positioning
  - Scroll wheel support

Try editing this text!
```

#### `_new_window`
```python
def _new_window(self) -> None
```
Creates a new simple window (Ctrl+N). Window is numbered sequentially.

#### `_cascade` / `_tile_h` / `_tile_v`
```python
def _cascade(self) -> None
def _tile_h(self) -> None
def _tile_v(self) -> None
```
Window arrangement operations using WindowManager.

#### `_show_open_dialog`
```python
def _show_open_dialog(self) -> None
```
Demonstrates OpenFileDialog with centered positioning.

#### `_show_save_dialog`
```python
def _show_save_dialog(self) -> None
```
Demonstrates SaveFileDialog with default name "untitled.txt".

#### `_show_about`
```python
def _show_about(self) -> None
```
Shows an about dialog with:
- Version information
- Feature list
- Centered on screen

---

## Running the Demo

```bash
cd /path/to/tui2
python examples/demo_app.py
```

---

## Demonstrated Widgets

| Widget | Description |
|--------|-------------|
| `Window` | Top-level windows with title bars |
| `Label` | Static text display |
| `Button` | Clickable buttons |
| `TextInput` | Single-line text input |
| `PasswordInput` | Masked password input |
| `Checkbox` | Boolean checkboxes |
| `RadioButton` | Radio button groups |
| `RadioGroup` | Groups radio buttons |
| `DropDownList` | Dropdown selection |
| `ListBox` | Scrollable list |
| `TextArea` | Multi-line text editor |
| `Calendar` | Date picker |
| `ProgressBar` | Progress indicator |
| `MenuBar` / `Menu` / `MenuItem` | Menu system |
| `MessageBox` | Message dialogs |
| `OpenFileDialog` | File open dialog |
| `SaveFileDialog` | File save dialog |
| `Container` | Widget container |
| `AbsoluteLayout` | Absolute positioning |

---

## Window Positions

| Window | Position | Size |
|--------|----------|------|
| Input Widgets | (2, 2) | 38x18 |
| List Demo | (42, 2) | 32x14 |
| Calendar | (42, 16) | 26x13 |
| Text Editor | (2, 20) | 38x12 |

---

## Key Bindings

| Key | Action |
|-----|--------|
| Ctrl+N | New Window |
| Ctrl+O | Open File Dialog |
| Ctrl+S | Save File Dialog |
| Ctrl+Q | Quit |
| Alt+Tab | Cycle windows |

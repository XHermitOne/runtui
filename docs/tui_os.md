# examples/tui_os.py - TUI-OS Desktop Environment

A macOS-like desktop environment running entirely in the terminal.

---

## Overview

TUI-OS is a complete desktop environment built with runtui that provides:
- **Finder**: File browser with copy/cut/paste/rename/delete
- **Terminal**: Real terminal emulator with PTY
- **Text Editor**: Multi-line text editor with syntax highlighting and save
- **Image Viewer**: Half-block rendered image viewer
- **Preferences**: Theme switching with persistence
- **macOS-style menus**: Menu bar changes based on active window

---

## Constants

### `VERSION`

```python
VERSION = "1.0.0"
```

### `EDITABLE_EXTENSIONS`

File extensions that open in the text editor:

```python
EDITABLE_EXTENSIONS = {
    ".txt", ".md", ".py", ".json", ".cfg", ".ini", ".toml",
    ".yaml", ".yml", ".log", ".sh", ".bash", ".zsh", ".conf",
    ".csv", ".xml", ".html", ".css", ".js", ".ts", ".c", ".h",
    ".cpp", ".hpp", ".rs", ".go", ".java", ".rb", ".pl",
}
```

### `IMAGE_EXTENSIONS`

Supported image formats:

```python
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp"}
```

---

## Functions

### `_move_to_trash`

```python
def _move_to_trash(path: Path) -> None
```

Move a file/directory to the platform's trash/recycle bin.

- **macOS**: Uses osascript to tell Finder to trash the item
- **Linux**: Follows XDG Trash spec (~/.local/share/Trash/)
- **Windows**: Falls back to permanent delete (or send2trash if available)

### `_load_config`

```python
def _load_config() -> dict
```

Load preferences from `tui_os.json`. Returns defaults if missing.

### `_save_config`

```python
def _save_config(config: dict) -> None
```

Save preferences to `tui_os.json`.

### `_find_wrapper`

```python
def _find_wrapper(app: "TuiOS", window: Window)
```

Find the wrapper object for a Window (FinderWindow, TerminalWindow, etc.).

### `_desktop_menu`

```python
def _desktop_menu(app: "TuiOS") -> MenuBar
```

Return the menu bar shown when no window is active.

---

## Classes

### `PreferencesDialog`

macOS-style Preferences dialog with theme selector.

#### Constructor

```python
def __init__(self, app: "TuiOS") -> None
```

#### Methods

| Method | Description |
|--------|-------------|
| `_on_theme_select` | Handle theme selection |
| `_on_theme_activate` | Switch to selected theme |
| `_on_cascade` | Cascade all windows |
| `_on_tile_h` | Tile windows horizontally |
| `_on_tile_v` | Tile windows vertically |

---

### `FinderWindow`

Creates and manages a Finder file browser window.

#### Constructor

```python
def __init__(self, app: "TuiOS", path: str | None = None) -> None
```

**Parameters:**
- `app` (`TuiOS`): Parent application
- `path` (`str | None`): Initial directory path

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `window` | `Window` | The managed window |
| `app` | `TuiOS` | Parent application |

#### Methods

| Method | Description |
|--------|-------------|
| `_refresh` | Refresh file listing |
| `_format_size` | Format file size for display |
| `_extract_name` | Extract filename from display item |
| `_on_file_activate` | Handle double-click on file |
| `_on_file_select` | Handle file selection |
| `_on_path_submit` | Navigate to entered path |
| `_on_close` | Clean up on window close |
| `_get_selected_paths` | Get full paths for selected items |
| `_copy` | Copy selected files to clipboard |
| `_cut` | Cut selected files to clipboard |
| `_paste` | Paste files from clipboard |
| `_delete` | Move selected files to trash |
| `_rename` | Rename selected file |
| `_navigate` | Navigate to directory |
| `get_menu` | Return Finder-specific menu bar |

#### Features

- Multi-select with Shift/Ctrl
- Copy/Cut/Paste operations
- Move to trash (platform-aware)
- Rename dialog with FormDialog
- Path navigation via text input
- Dynamic resize layout

---

### `TerminalWindow`

Creates and manages a Terminal emulator window.

#### Constructor

```python
def __init__(self, app: "TuiOS", command: str = "") -> None
```

**Parameters:**
- `app` (`TuiOS`): Parent application
- `command` (`str`): Optional command to run

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `window` | `Window` | The managed window |
| `_terminal` | `TerminalWidget` | The terminal widget |

#### Methods

| Method | Description |
|--------|-------------|
| `_on_close` | Stop terminal and clean up |
| `_copy` | Copy selection to clipboard |
| `_clear` | Send clear command to terminal |
| `get_menu` | Return Terminal-specific menu bar |

#### Features

- Real PTY terminal emulation via pyte
- Full keyboard input forwarding
- Mouse scrolling support
- Process exit detection
- Text selection with copy

---

### `EditorWindow`

Creates and manages a Text Editor window.

#### Constructor

```python
def __init__(self, app: "TuiOS", filepath: str = "") -> None
```

**Parameters:**
- `app` (`TuiOS`): Parent application
- `filepath` (`str`): File to edit

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `window` | `Window` | The managed window |
| `_filepath` | `str` | Current file path |
| `_dirty` | `bool` | Has unsaved changes |
| `_textarea` | `TextArea` | The text editor widget |

#### Methods

| Method | Description |
|--------|-------------|
| `_load_file` | Load file into editor |
| `_on_text_change` | Mark document as dirty |
| `_update_title` | Update window title with dirty marker |
| `save` | Save current file |
| `_on_close` | Clean up on window close |
| `get_menu` | Return Editor-specific menu bar |

#### Features

- Multi-line editing with TextArea
- Syntax highlighting based on file extension
- Dirty marker (*) in title
- Dynamic resize layout
- Save functionality

---

### `ImageViewerWindow`

Creates and manages an Image Viewer window.

#### Constructor

```python
def __init__(self, app: "TuiOS", filepath: str) -> None
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `window` | `Window` | The managed window |
| `_image_widget` | `ImageWidget` | The image widget |
| `_filepath` | `str` | Current image path |

#### Methods

| Method | Description |
|--------|-------------|
| `_on_close` | Clean up on window close |
| `_zoom_in` | Zoom in on image |
| `_zoom_out` | Zoom out on image |
| `_fit` | Fit image to window |
| `_actual` | Reset to actual size |
| `get_menu` | Return Image Viewer menu bar |

#### Features

- Half-block rendering (2x vertical resolution)
- Zoom controls (+/-/0/1)
- Pan with arrow keys

---

### `LoadedAppWindowWrapper`

Wrapper for windows created by loaded .py files, providing a safe menu.

#### Constructor

```python
def __init__(self, app: "TuiOS", window: Window, foreign_app=None) -> None
```

#### Methods

| Method | Description |
|--------|-------------|
| `_close_all_windows` | Close all windows from the foreign app |
| `_is_quit_label` | Check if label is Quit/Exit |
| `_patch_menu_items` | Replace Exit/Quit with Close |
| `get_menu` | Return wrapped menu bar |

---

### `TuiOS`

Main application class - macOS-like terminal desktop environment.

#### Constructor

```python
def __init__(self) -> None
```

Loads configuration from `tui_os.json` and initializes theme.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `_config` | `dict` | Loaded configuration |
| `_finder_windows` | `list[FinderWindow]` | Open Finder windows |
| `_terminal_windows` | `list[TerminalWindow]` | Open Terminal windows |
| `_editor_windows` | `list[EditorWindow]` | Open Editor windows |
| `_image_windows` | `list[ImageViewerWindow]` | Open Image windows |
| `_loaded_app_windows` | `dict[Window, object]` | Windows from loaded .py files |
| `_active_wrapper` | `object` | Current active window wrapper |
| `_clipboard` | `list[tuple[str, str]]` | Clipboard (path, operation) |

#### Methods

| Method | Description |
|--------|-------------|
| `set_theme` | Switch theme and persist to config |
| `on_ready` | Initialize desktop with Finder |
| `_tick` | Periodic check for dead processes |
| `_system_menu` | Return the persistent system menu |
| `_cascade_windows` | Cascade all windows |
| `_tile_h_windows` | Tile windows horizontally |
| `_tile_v_windows` | Tile windows vertically |
| `_update_menu_for_window` | Switch menu bar for active window |
| `_open_finder` | Create new Finder window |
| `_open_terminal` | Create new Terminal window |
| `_open_terminal_with_command` | Create Terminal with command |
| `_open_editor` | Create new Editor window |
| `_open_image_viewer` | Create new Image Viewer window |
| `_on_finder_open_file` | Open file based on extension |
| `_run_py_file` | Execute .py file in-process |
| `_run_rad_json` | Load RAD design JSON |
| `_show_error` | Show error message box |
| `_listen_window_events` | Register window event handlers |
| `_on_window_event` | Handle window events |
| `_refresh_menu_after_close` | Update menu after window closes |
| `_show_preferences` | Open Preferences dialog |
| `_show_about` | Show About dialog |
| `_is_terminal_focused` | Check if TerminalWidget is focused |
| `_handle_key` | Handle global keyboard shortcuts |
| `_shutdown` | Clean up all terminal processes |

#### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Finder window |
| Ctrl+T | New Terminal window |
| Ctrl+W | Close active window |
| Ctrl+S | Save (in Editor) |
| Ctrl+Q | Quit TUI-OS |
| F5 | Refresh Finder |
| Alt+Tab | Cycle windows |

---

## Configuration

Configuration is saved to `examples/tui_os.json`:

```json
{
  "theme": "light"
}
```

---

## Running TUI-OS

```bash
cd /path/to/tui2
python examples/tui_os.py
```

---

## Architecture

TUI-OS implements a macOS-style desktop:

1. **Window Management**: Windows are managed by `WindowManager` with z-ordering, focus, and tiling
2. **Menu Bar Switching**: The global menu bar changes based on which window is active
3. **File Type Dispatch**: Files open in appropriate app based on extension
4. **In-Process Python Execution**: .py files with App subclasses run in the same process
5. **RAD Integration**: JSON design files can be previewed directly
6. **Terminal Passthrough**: When TerminalWidget is focused, most keys go directly to the shell

---

## In-Process Python Execution

When a `.py` file is opened from Finder, TUI-OS can execute it in-process rather than spawning a subprocess. This allows the loaded application's windows to integrate seamlessly with the TUI-OS desktop.

### User Flow

1. Double-click a `.py` file in Finder
2. A MessageBox asks: "How would you like to open {filename}?"
3. User chooses **Run** or **Edit**
   - **Run**: Execute in-process (if App subclass found)
   - **Edit**: Open in the text editor

### Execution Process (`_run_py_file`)

```python
def _run_py_file(self, filepath: str) -> None
```

#### Step 1: Read and Compile

```python
with open(filepath, "r", encoding="utf-8") as f:
    source = f.read()

namespace = {
    "__name__": "__loaded__",  # NOT "__main__" — prevents auto-run
    "__file__": filepath,
}

exec(compile(source, filepath, "exec"), namespace)
```

The file is executed with `__name__ = "__loaded__"` to prevent any `if __name__ == "__main__"` blocks from running automatically.

#### Step 2: Find App Subclass

```python
for obj in namespace.values():
    if (isinstance(obj, type)
            and issubclass(obj, App)
            and obj is not App
            and obj is not TuiOS):
        app_class = obj
        break
```

Looks for a class that inherits from `App` (but is not `App` or `TuiOS` itself).

#### Step 3: Instantiate and Redirect

```python
foreign_app = app_class()

# Redirect framework internals
foreign_app._window_manager = self._window_manager
foreign_app._theme_engine = self._theme_engine
foreign_app._screen = self._screen
foreign_app._event_loop = self._event_loop
foreign_app.root = self.root
```

The foreign app's internals are redirected to use TUI-OS's infrastructure.

#### Step 4: Intercept Window Creation

```python
def _capture_add_window(window, activate=True):
    captured_windows.append(window)
    window.title = f"[{filename}] {window.title}"  # Prefix title
    self.add_window(window)
    self._listen_window_events(window)
    self._loaded_app_windows[window] = foreign_app
    self._update_menu_for_window(window)

foreign_app.add_window = _capture_add_window
```

All `add_window` calls are intercepted so windows are added to TUI-OS's desktop.

#### Step 5: Intercept Menu and Quit

```python
def _capture_set_menu(menu_bar):
    foreign_app._captured_menu = menu_bar

foreign_app.set_menu = _capture_set_menu
foreign_app.quit = lambda *a, **kw: None  # Ignore quit calls
```

Menu bars are captured for per-window menu switching. Quit calls are ignored to prevent the loaded app from closing TUI-OS.

#### Step 6: Call on_ready

```python
if hasattr(foreign_app, 'on_ready'):
    foreign_app.on_ready()
```

Finally, `on_ready()` is called to create the app's windows.

### Window Title Prefixing

Windows from loaded apps have their titles prefixed with the filename:

```
[my_app.py] My Application
```

### Menu Bar Integration

When a window from a loaded app becomes active, its menu bar is shown. The `LoadedAppWindowWrapper` patches the menu items:

- **Exit** / **Quit** items are replaced with **Close**
- The close action only closes that app's windows, not TUI-OS

### Fallback Behavior

If the `.py` file:
- Has no `App` subclass → Shows error, opens in text editor instead
- Has syntax errors → Shows error message
- Creates no windows → Shows error message

### Example: Loading a Demo App

Given `examples/demo_app.py`:

```python
class DemoApp(App):
    def on_ready(self):
        self._create_input_demo()
        self._create_list_demo()
        ...

if __name__ == "__main__":
    app = DemoApp()
    app.run()
```

When loaded in TUI-OS:
1. `DemoApp` class is found
2. Instance created, internals redirected
3. `on_ready()` creates windows on TUI-OS desktop
4. Windows have titles like `[demo_app.py] Input Widgets`
5. Menu bar switches when DemoApp windows are active
6. Closing all DemoApp windows returns to TUI-OS

# TUI-OS: macOS-like Terminal Operating System

## Overview

TUI-OS is a macOS-inspired desktop environment that runs entirely in the terminal, built on the **runtui** framework. It provides a Finder (file browser), Terminal emulator (real PTY), Text Editor, and Preferences dialog, with per-window menu bar switching that mirrors macOS behavior.

## Quick Start

```bash
python examples/tui_os.py
```

## Architecture

```
TuiOS (subclass of App)
├── Global Menu Bar (swaps per active window)
├── Desktop (background pattern widget)
├── WindowManager
│   ├── FinderWindow(s) — file browser
│   ├── TerminalWindow(s) — real PTY shell
│   ├── EditorWindow(s) — text file editor
│   └── (extensible for future window types)
├── TaskBar (bottom, shows windows + clock)
└── Dialogs
    ├── PreferencesDialog (theme, window arrangement)
    └── About MessageBox
```

## Components

### 1. TerminalWidget (`runtui/widgets/terminal.py`)

Pipe-based terminal emulator with two modes:

- **Shell mode** (no command): Displays `$ ` prompt, user types commands, each command runs as a hidden subprocess (`subprocess.Popen` with `stdout=PIPE, stderr=STDOUT, stdin=DEVNULL`). Background reader thread captures output and appends to display buffer. Tracks working directory via built-in `cd`.
- **Command mode** (command given): Runs the single command, streams output, shows exit code when done.
- **No PTY needed**: Since the TUI app already owns the real terminal, subprocesses use pipes — completely avoids PTY/controlling-terminal conflicts.
- **Reader thread**: Background `threading.Thread` reads subprocess stdout pipe and appends to display lines.
- **ANSI stripping**: Strips CSI and OSC escape sequences from subprocess output for clean display (sets `TERM=dumb` and `NO_COLOR=1`).
- **Built-in commands**: `cd` (with directory tracking), `clear` (screen reset), `exit`/`quit`.
- **Features**: Command history (Up/Down arrows), tab completion (files/directories), Ctrl+C to kill running process, Ctrl+L to clear, Ctrl+U to clear input line.
- **Cross-platform**: Works on Unix, macOS, and Windows — no platform-specific code.

### 2. Finder Window

File browser starting from the current working directory:

- **Navigation**: Enter/double-click to open, `..` to go up, path bar for direct entry
- **File display**: Directories (📁) first, then files (📄) with sizes, hidden files excluded
- **File actions**:
  - `.py` files → **run in-process**: exec the file, find its `App` subclass, call `on_ready()`, inject its windows into TUI-OS (prefixed with `[filename]`). When closed, windows are simply removed.
  - `.json` files → detect RAD designs and load via `preview_in_app()` (in-process), otherwise open in editor
  - Text files (`.txt`, `.md`, etc.) → open in Text Editor
  - All other files → attempt to open as text
- **Status bar**: Shows item count and selected file info

### 3. Terminal Window

Window wrapping the TerminalWidget:

- Spawns an interactive shell by default
- Can launch with a specific command (e.g., `python3 script.py`)
- Per-window menu: Shell (New Terminal, Close), Edit (Clear Screen)
- Multiple terminal windows supported simultaneously

### 4. Text Editor Window

Simple text file editor:

- TextArea widget for multi-line editing with undo/redo
- File load/save with dirty tracking (title shows `*` for unsaved changes)
- Per-window menu: Application (Save, Close), Edit (Undo, Redo, Select All)
- Status bar showing file path and save status
- Deduplication: opening an already-open file activates its existing window

### 5. Per-Window Menu Bar (macOS-style)

When a window becomes active, the global menu bar swaps to show that window's menus:

- **TUI menu** (leftmost, always present): About, Preferences, Window Arrangement (Cascade/Tile H/Tile V), Quit
- **Finder menus**: Application (New Finder, New Terminal, Close), Go (Home, Parent, Root, Refresh)
- **Terminal menus**: Shell (New Terminal, New Finder, Close), Edit (Clear Screen)
- **Editor menus**: Application (Save, New Finder, New Terminal, Close), Edit (Undo, Redo, Select All)
- **Desktop menu**: Shown when no windows are active — Application (New Finder, New Terminal, Quit)

Implementation: Each wrapper class (`FinderWindow`, `TerminalWindow`, `EditorWindow`) has a `get_menu()` method that returns a full `MenuBar`. On `WindowAction.ACTIVATE` events, `TuiOS._update_menu_for_window()` looks up the wrapper and calls `self.set_menu(wrapper.get_menu())`.

### 6. Preferences Dialog

Modal dialog with:

- **Theme selector**: Lists all registered themes, click to apply immediately
- **Window arrangement**: Cascade, Tile Horizontal, Tile Vertical buttons

### 7. About Dialog

MessageBox showing version, features, and keyboard shortcuts.

## Keyboard Shortcuts

| Shortcut  | Action                    |
|-----------|---------------------------|
| Ctrl+N    | New Finder window         |
| Ctrl+T    | New Terminal window       |
| Ctrl+W    | Close active window       |
| Ctrl+S    | Save (in Editor)          |
| Ctrl+Q    | Quit TUI-OS              |
| Alt+Tab   | Cycle windows             |
| F5        | Refresh Finder            |
| F10       | Activate menu bar         |

## Themes

Available themes: Turbo Vision, Dark, Light, Nord, Solarized. Change via Preferences dialog or system menu.

## File Structure

| File | Description |
|------|-------------|
| `examples/tui_os.py` | Main application (~500 lines) |
| `examples/tui_os.md` | This design document |
| `runtui/widgets/terminal.py` | PTY-based terminal widget (~640 lines) |

## Design Decisions

1. **Pipe-based subprocess over PTY**: Since the TUI app already owns the real terminal (raw mode stdin), using a PTY for child shells creates conflicts. Instead, each command is a hidden subprocess with pipes. The widget simulates a shell prompt, manages its own input line, command history, tab completion, and `cd` tracking — all without needing a PTY. The child process gets a proper controlling terminal via `setsid()` + `TIOCSCTTY`, and the slave PTY has sane termios attributes set before spawning.
2. **Per-window menus**: Mirrors macOS UX where the menu bar changes based on the active application/window.
3. **In-process app loading**: `.py` files from Finder are exec'd in-process. Their `App` subclass is instantiated, `add_window` is redirected to inject windows into TUI-OS, and `on_ready()` is called. This means loaded apps share the same event loop, theme engine, and window manager — their windows appear as native TUI-OS windows. When closed, they're simply removed with no cleanup burden.
4. **Thread-safe terminal**: Reader thread + lock + deque pattern ensures the UI never blocks on shell output while remaining safe for concurrent access.
5. **Wrapper pattern**: Each window type is a plain class wrapping a `Window` instance rather than subclassing, keeping the integration clean and allowing multiple instances.
6. **Key dispatch bypass for Terminal**: The base `App._handle_key` intercepts Tab (focus cycling), Escape (menu blur), etc. before dispatching to widgets. When a TerminalWidget is focused, `TuiOS._handle_key` bypasses this and sends all non-global-shortcut keys directly to the terminal, so the shell receives Tab, Escape, arrow keys, etc.
7. **Auto-focus on window creation**: Each window type focuses its primary widget (TerminalWidget, ListBox, TextArea) immediately on creation so it's interactive without requiring a click first.

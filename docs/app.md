# app.py - Application Class

The main application class that manages the terminal UI lifecycle, event loop, and rendering.

---

## Class: `Desktop`

Desktop background widget that fills with a checkerboard pattern.

### Methods

#### `paint`
```python
def paint(self, painter: Painter) -> None
```
Draw the desktop background with alternating character pattern.

---

## Class: `App`

The base class for runtui applications. Handles terminal setup, event processing, and rendering.

### Constructor

```python
def __init__(self, theme: str = "turbo_vision") -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `theme` | `str` | `"turbo_vision"` | Theme name to use |

### Available Themes

- `"turbo_vision"` - Classic DOS-era look (default)
- `"github"` - GitHub-inspired light theme
- `"vscode"` - VS Code dark theme
- `"gruvbox"` - Gruvbox dark theme
- `"high_contrast"` - High contrast accessibility
- `"legacy_system"` - DOS/BIOS theme
- `"black_white"` - Monochrome theme
- `"dark"` - Dark theme
- `"light"` - Light theme
- `"nord"` - Nord color scheme
- `"solarized"` - Solarized theme

### Properties

#### `running`
```python
@property
def running(self) -> bool
```
Returns `True` if the application is currently running.

### Methods

#### `run`
```python
def run(self) -> None
```
Start the application main loop. Blocks until `quit()` is called.

#### `quit`
```python
def quit(self) -> None
```
Stop the application and restore the terminal to normal mode.

#### `on_ready`
```python
def on_ready(self) -> None
```
Callback called after the application is initialized and ready. Override this method to set up your UI.

#### `add_window`
```python
def add_window(self, window: Window) -> None
```
Add a window to the desktop.

**Parameters:**
- `window` (`Window`): The window to add

#### `remove_window`
```python
def remove_window(self, window: Window) -> None
```
Remove a window from the desktop.

**Parameters:**
- `window` (`Window`): The window to remove

#### `set_menu`
```python
def set_menu(self, menu_bar: MenuBar) -> None
```
Set the application menu bar.

**Parameters:**
- `menu_bar` (`MenuBar`): The menu bar widget to use

#### `invalidate_all`
```python
def invalidate_all(self) -> None
```
Force a full repaint of the screen.

#### `set_theme`
```python
def set_theme(self, name: str) -> None
```
Change the active theme.

**Parameters:**
- `name` (`str`): Theme name to activate

#### `call_later`
```python
def call_later(self, delay: float, callback: Callable[[], None]) -> TimerHandle | None
```
Schedule a callback to be executed after a delay.

**Parameters:**
- `delay` (`float`): Delay in seconds
- `callback` (`Callable[[], None]`): The function to call

**Returns:** `TimerHandle | None` - Handle to cancel the timer

#### `set_interval`
```python
def set_interval(self, interval: float, callback: Callable[[], None]) -> TimerHandle | None
```
Start a repeating timer.

**Parameters:**
- `interval` (`float`): Interval in seconds
- `callback` (`Callable[[], None]`): Function to call on each tick

**Returns:** `TimerHandle | None` - Handle to stop the timer

### Global Key Bindings

| Key | Action |
|-----|--------|
| Ctrl+Q | Quit application |
| Alt+Tab | Cycle to next window |
| Alt+Shift+Tab | Cycle to previous window |
| Tab | Focus next widget |
| Shift+Tab | Focus previous widget |
| F10 | Activate menu bar |

### Usage

```python
from runtui import App, Window, Label

class MyApp(App):
    def __init__(self):
        super().__init__(theme="turbo_vision")

    def on_ready(self):
        window = Window(title="My App")
        window.set_content(Label("Hello, World!"))
        self.add_window(window)

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

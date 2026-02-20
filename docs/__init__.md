# runtui Package

The main runtui package exports the core classes and widgets for building terminal user interfaces.

## Exports

The following classes and functions are exported from the main package:

| Name | Module | Description |
|------|--------|-------------|
| `App` | `app` | Main application class for running TUI applications |
| `Window` | `windows.window` | Top-level window widget with title bar and chrome |
| `MenuBar` | `widgets.menu` | Top-level menu bar widget |
| `Menu` | `widgets.menu` | Dropdown menu container |
| `MenuItem` | `widgets.menu` | Individual menu item |
| `RadioGroup` | `widgets.radio` | Group container for radio buttons |

## Usage

```python
from runtui import App, Window

class MyApp(App):
    def on_ready(self):
        window = Window(title="My Window")
        self.add_window(window)

app = MyApp()
app.run()
```

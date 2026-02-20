# widgets/menu.py - Menu Widgets

Menu bar and dropdown menu widgets.

---

## Class: `MenuBar`

Top-level menu bar widget.

### Constructor

```python
def __init__(
    self,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 0,
) -> None
```

### Methods

#### `add_menu`
```python
def add_menu(self, menu: Menu) -> None
```
Add a dropdown menu to the bar.

---

## Class: `Menu`

A dropdown menu container.

### Constructor

```python
def __init__(
    self,
    label: str = "Menu",
    id: str | None = None,
) -> None
```

**Parameters:**
- `label` (`str`): Menu label displayed in menu bar

### Methods

#### `add_item`
```python
def add_item(
    self,
    label: str,
    on_click: Callable[[], None] | None = None,
    shortcut: str = "",
) -> MenuItem
```
Add a menu item.

#### `add_separator`
```python
def add_separator(self) -> None
```
Add a separator line.

---

## Class: `MenuItem`

A single menu item.

### Constructor

```python
def __init__(
    self,
    label: str = "",
    on_click: Callable[[], None] | None = None,
    shortcut: str = "",
    enabled: bool = True,
) -> None
```

**Parameters:**
- `label` (`str`): Item label
- `on_click` (`Callable[[], None]`): Click callback
- `shortcut` (`str`): Keyboard shortcut hint (display only)
- `enabled` (`bool`): Whether item is enabled

### Usage

```python
menubar = MenuBar()
file_menu = Menu("File")
file_menu.add_item("New", on_new, "Ctrl+N")
file_menu.add_item("Open...", on_open, "Ctrl+O")
file_menu.add_separator()
file_menu.add_item("Exit", on_exit)
menubar.add_menu(file_menu)
```
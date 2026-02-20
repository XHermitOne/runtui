# widgets/context_menu.py - ContextMenu Widget

Right-click context menu.

---

## Class: `ContextMenu`

A popup context menu that appears at a specific location.

### Constructor

```python
def __init__(
    self,
    x: int = 0,
    y: int = 0,
) -> None
```

**Parameters:**
- `x` (`int`): Initial X position
- `y` (`int`): Initial Y position

### Methods

#### `add_item`
```python
def add_item(
    self,
    label: str,
    on_click: Callable[[], None] | None = None,
) -> MenuItem
```
Add a menu item.

#### `add_separator`
```python
def add_separator(self) -> None
```
Add a separator line.

#### `show`
```python
def show(self, x: int, y: int) -> None
```
Show the menu at the specified position.

#### `hide`
```python
def hide(self) -> None
```
Hide the menu.

### Usage

```python
def show_context_menu(event):
    menu = ContextMenu()
    menu.add_item("Copy", on_copy)
    menu.add_item("Paste", on_paste)
    menu.show(event.x, event.y)
```
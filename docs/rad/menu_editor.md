# rad/menu_editor.py - Menu Editor

Visual menu structure editor.

---

## Class: `MenuEditor`

A visual editor for menu structures.

### Constructor

```python
def __init__(self) -> None
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `menubar` | `MenuBarSchema \| None` | The menu bar being edited |
| `selected` | `MenuItemSchema \| None` | Currently selected item |

### Methods

#### `add_menu`
```python
def add_menu(self, label: str) -> MenuSchema
```
Add a top-level menu.

**Parameters:**
- `label` (`str`): Menu label

**Returns:** `MenuSchema` - The created menu

#### `add_item`
```python
def add_item(
    self,
    menu: MenuSchema,
    label: str,
    shortcut: str = "",
) -> MenuItemSchema
```
Add a menu item to a menu.

**Parameters:**
- `menu` (`MenuSchema`): Parent menu
- `label` (`str`): Item label
- `shortcut` (`str`): Keyboard shortcut hint

**Returns:** `MenuItemSchema` - The created item

#### `add_separator`
```python
def add_separator(self, menu: MenuSchema) -> None
```
Add a separator to a menu.

**Parameters:**
- `menu` (`MenuSchema`): Parent menu

#### `remove_selected`
```python
def remove_selected(self) -> None
```
Remove the currently selected item.

#### `move_selected_up` / `move_selected_down`
```python
def move_selected_up(self) -> None
def move_selected_down(self) -> None
```
Move the selected item within its menu.

#### `get_schema`
```python
def get_schema(self) -> MenuBarSchema | None
```
Get the complete menu bar schema.

**Returns:** `MenuBarSchema | None` - The menu bar schema
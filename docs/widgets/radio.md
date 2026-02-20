# widgets/radio.py - RadioButton Widgets

Radio button selection widgets.

---

## Class: `RadioGroup`

Groups RadioButtons so only one can be selected at a time.

### Constructor

```python
def __init__(self, on_change: Callable[[str], None] | None = None) -> None
```

**Parameters:**
- `on_change` (`Callable[[str], None]`): Callback when selection changes

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `selected` | `RadioButton \| None` | Currently selected button |
| `selected_value` | `str` | Value of selected button |

### Methods

#### `add`
```python
def add(self, button: RadioButton) -> None
```
Add a radio button to the group.

#### `select`
```python
def select(self, button: RadioButton) -> None
```
Select a radio button programmatically.

---

## Class: `RadioButton`

A radio button with a label, part of a RadioGroup.

### Constructor

```python
def __init__(
    self,
    label: str = "",
    value: str = "",
    selected: bool = False,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 0,
    group: RadioGroup | None = None,
) -> None
```

**Parameters:**
- `label` (`str`): Display label
- `value` (`str`): Value returned when selected (defaults to label)
- `selected` (`bool`): Initial selection state
- `group` (`RadioGroup | None`): Parent group

### Properties

#### `selected`
```python
@property
def selected(self) -> bool
```
Whether this button is selected.

### Methods

#### `select`
```python
def select(self) -> None
```
Select this radio button.

### Theme Glyphs

| Slot | Default |
|------|---------|
| `radio.selected` | `(*)` |
| `radio.unselected` | `( )` |

### Usage

```python
group = RadioGroup(on_change=lambda v: print(f"Selected: {v}"))
rb1 = RadioButton("Option 1", value="opt1", group=group)
rb2 = RadioButton("Option 2", value="opt2", group=group)
```
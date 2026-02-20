# layout/box.py - Box Layouts

Horizontal and vertical box layouts for linear widget arrangement.

---

## Class: `HBoxLayout`

Horizontal box layout -- children arranged left to right.

Children with `flex > 0` share remaining space proportionally.
Children with `flex == 0` use their measured width.

### Constructor

```python
def __init__(self, spacing: int = 0) -> None
```

**Parameters:**
- `spacing` (`int`): Pixels/columns between children

### Methods

#### `measure`
```python
def measure(self, container: Widget, available: Size) -> Size
```
Calculate desired size: sum of child widths, max child height.

#### `arrange`
```python
def arrange(self, container: Widget, rect: Rect) -> None
```
Position children horizontally.

### Flex Layout

Children can have a `flex` attribute:
- `flex = 0` (default): Child uses its measured width
- `flex > 0`: Child shares remaining space proportionally

```python
container = Container(layout=HBoxLayout(spacing=1))
container.add(Label("Fixed"))  # Uses measured width
container.add(Label("Flexible", flex=1))  # Takes remaining space
```

---

## Class: `VBoxLayout`

Vertical box layout -- children arranged top to bottom.

Children with `flex > 0` share remaining space proportionally.
Children with `flex == 0` use their measured height.

### Constructor

```python
def __init__(self, spacing: int = 0) -> None
```

**Parameters:**
- `spacing` (`int`): Rows between children

### Methods

#### `measure`
```python
def measure(self, container: Widget, available: Size) -> Size
```
Calculate desired size: max child width, sum of child heights.

#### `arrange`
```python
def arrange(self, container: Widget, rect: Rect) -> None
```
Position children vertically.

### Usage

```python
form = Container(layout=VBoxLayout(spacing=1))
form.add(Label("Name:"))
form.add(TextInput())
form.add(Label("Email:"))
form.add(TextInput())
form.add(Button("Submit", flex=0))  # Fixed height
```
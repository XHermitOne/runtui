# layout/grid.py - Grid Layout

Grid layout with rows and columns.

---

## Class: `GridLayout`

Grid layout with specified rows and columns.

Children are placed left-to-right, top-to-bottom. Each child can have `grid_row`, `grid_col`, `grid_row_span`, `grid_col_span` attributes. If not set, children are auto-placed sequentially.

### Constructor

```python
def __init__(
    self,
    rows: int = 1,
    cols: int = 1,
    h_gap: int = 0,
    v_gap: int = 0,
) -> None
```

**Parameters:**
- `rows` (`int`): Number of rows (minimum 1)
- `cols` (`int`): Number of columns (minimum 1)
- `h_gap` (`int`): Horizontal gap between columns
- `v_gap` (`int`): Vertical gap between rows

### Methods

#### `measure`
```python
def measure(self, container: Widget, available: Size) -> Size
```
Returns the available size.

#### `arrange`
```python
def arrange(self, container: Widget, rect: Rect) -> None
```
Position children in the grid.

### Child Attributes

Children can specify grid placement:

| Attribute | Description |
|-----------|-------------|
| `grid_row` | Row index (0-based) |
| `grid_col` | Column index (0-based) |
| `grid_row_span` | Number of rows to span |
| `grid_col_span` | Number of columns to span |

If not specified, children are placed automatically left-to-right, then top-to-bottom.

### Usage

```python
grid = Container(layout=GridLayout(rows=3, cols=2, h_gap=2, v_gap=1))

# Auto-placed (row 0, col 0)
grid.add(Label("Name:"))
grid.add(TextInput())

# Auto-placed (row 1, col 0)
grid.add(Label("Email:"))
grid.add(TextInput())

# Manual placement with spanning
button = Button("Submit", grid_row=2, grid_col=0, grid_col_span=2)
grid.add(button)
```
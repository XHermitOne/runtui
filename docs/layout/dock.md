# layout/dock.py - Dock Layout

Layout that docks children to edges.

---

## Class: `DockLayout`

Layout that docks children to top/bottom/left/right/fill.

Each child's `dock` attribute determines placement:
- `"top"` - Full width, at top of remaining space
- `"bottom"` - Full width, at bottom of remaining space
- `"left"` - Full height, at left of remaining space
- `"right"` - Full height, at right of remaining space
- `"fill"` - Fills all remaining space (should be last)

Children are processed in order, each reducing the remaining space.

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
Position children according to their dock attribute.

### Usage

```python
container = Container(layout=DockLayout())

# Header at top
header = Label("Header", dock="top", height=3)
container.add(header)

# Footer at bottom
footer = Label("Footer", dock="bottom", height=2)
container.add(footer)

# Main content fills remaining space
content = Container(dock="fill")
container.add(content)
```

### Dock Order

The order of children matters:
1. Top-docked children are placed first at the top
2. Bottom-docked children are placed at the bottom
3. Left-docked children are placed on the left
4. Right-docked children are placed on the right
5. Fill children get the remaining space
# layout/base.py - Layout Manager Protocol

Abstract base class for layout managers.

---

## Class: `LayoutManager`

Abstract base for layout managers.

### Abstract Methods

#### `measure`
```python
@abstractmethod
def measure(self, container: Widget, available: Size) -> Size
```
Calculate the desired size for the container.

**Parameters:**
- `container` (`Widget`): The container widget
- `available` (`Size`): Available size for the container

**Returns:** `Size` - The desired size

#### `arrange`
```python
@abstractmethod
def arrange(self, container: Widget, rect: Rect) -> None
```
Position children within the given rectangle.

**Parameters:**
- `container` (`Widget`): The container widget
- `rect` (`Rect`): The rectangle to arrange children within
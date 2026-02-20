# widgets/static_image.py - StaticImage Widget

A simple image display widget without interactive controls.

---

## Class: `StaticImage`

Renders an image fit-to-size using half-block Unicode characters.

Each character cell displays 2 vertical pixels using '▄' (lower half block):
- background color = top pixel
- foreground color = bottom pixel

The entire widget area is used for the image (no toolbar).
The image is automatically scaled to fit the widget dimensions.

### Constructor

```python
def __init__(
    self,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 40,
    height: int = 20,
    filepath: str = "",
) -> None
```

**Parameters:**
- `id` (`str | None`): Widget identifier
- `x` (`int`): X position
- `y` (`int`): Y position
- `width` (`int`): Width in columns
- `height` (`int`): Height in rows
- `filepath` (`str`): Path to image file to load

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `can_focus` | `bool` | Always `False` (non-interactive) |

### Methods

#### `load`
```python
def load(self, filepath: str) -> bool
```

Load an image file. Returns `True` on success.

**Parameters:**
- `filepath` (`str`): Path to the image file

**Returns:** `bool` - `True` if loaded successfully

#### `measure`
```python
def measure(self, available: Size) -> Size
```
Return the size needed for the image.

#### `paint`
```python
def paint(self, painter: Painter) -> None
```
Draw the image using half-block characters.

### Image Scaling

The image is automatically scaled to fit within the widget dimensions while preserving aspect ratio. The image is centered on a black background.

### Requirements

Requires Pillow (PIL) for image loading and scaling. If PIL is not available, the widget displays "PIL not available" message.

### Supported Formats

Any format supported by Pillow (PNG, JPEG, GIF, BMP, etc.).

### Usage

```python
image = StaticImage(
    filepath="/path/to/image.png",
    width=40,
    height=20,
)
container.add_child(image)

# Or load later
image = StaticImage(width=40, height=20)
image.load("/path/to/image.png")
```

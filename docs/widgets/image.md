# widgets/image.py - ImageWidget

Image display widget.

---

## Class: `ImageWidget`

A widget for displaying images in the terminal.

### Constructor

```python
def __init__(
    self,
    path: str | None = None,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 0,
    height: int = 0,
) -> None
```

**Parameters:**
- `path` (`str | None`): Path to the image file
- `width` (`int`): Display width (0 = auto)
- `height` (`int`): Display height (0 = auto)

### Properties

#### `path`
```python
@property
def path(self) -> str | None
```
Path to the current image.

### Methods

#### `load`
```python
def load(self, path: str) -> None
```
Load an image from a file path.

### Terminal Support

Image display requires terminal support for one of:
- Sixel graphics
- Kitty graphics protocol
- iTerm2 inline images
- ASCII art fallback

### Usage

```python
image = ImageWidget(path="/path/to/image.png", width=40, height=20)
```
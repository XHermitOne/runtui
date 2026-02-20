# widgets/progressbar.py - ProgressBar Widget

Progress indicator widget.

---

## Class: `ProgressBar`

A progress bar widget for showing progress.

### Constructor

```python
def __init__(
    self,
    value: float = 0.0,
    minimum: float = 0.0,
    maximum: float = 100.0,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    width: int = 20,
) -> None
```

**Parameters:**
- `value` (`float`): Current value
- `minimum` (`float`): Minimum value
- `maximum` (`float`): Maximum value

### Properties

#### `value`
```python
@property
def value(self) -> float
```
Current progress value.

```python
@value.setter
def value(self, v: float) -> None
```
Set the value (clamped to min/max).

#### `percentage`
```python
@property
def percentage(self) -> float
```
Progress as percentage (0-100).

### Theme Glyphs

| Slot | Default |
|------|---------|
| `progressbar.fill` | `█` |
| `progressbar.empty` | `░` |

### Usage

```python
progress = ProgressBar(width=40)
progress.value = 50  # 50%
```
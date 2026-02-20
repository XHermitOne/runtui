# themes/engine.py - Theme Engine

Theme engine for managing colors and glyphs.

---

## Class: `ThemeEngine`

Manages theme colors and glyphs with fallback support.

### Constructor

```python
def __init__(self, name: str = "light") -> None
```

**Parameters:**
- `name` (`str`): Theme name to load

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Current theme name |

### Methods

#### `color`
```python
def color(self, slot: str, fallback: Color = Color.DEFAULT) -> Color
```
Get a color from the theme.

**Parameters:**
- `slot` (`str`): Color slot name (e.g., `"button.bg"`, `"label.fg"`)
- `fallback` (`Color`): Default color if slot not found

**Returns:** `Color` - The color for that slot

#### `glyph`
```python
def glyph(self, slot: str, fallback: str = "") -> str
```
Get a glyph/character from the theme.

**Parameters:**
- `slot` (`str`): Glyph slot name
- `fallback` (`str`): Default glyph if not found

**Returns:** `str` - The glyph

#### `load_theme`
```python
def load_theme(self, name: str) -> None
```
Load a theme by name.

### Color Slots

Common color slots:

| Slot | Description |
|------|-------------|
| `bg` | Default background |
| `fg` | Default foreground |
| `label.fg` | Label text color |
| `button.fg` | Button text color |
| `button.bg` | Button background |
| `button.focused.fg` | Focused button text |
| `button.focused.bg` | Focused button background |
| `input.fg` | Input text color |
| `input.bg` | Input background |
| `input.focused.fg` | Focused input text |
| `input.focused.bg` | Focused input background |
| `window.title` | Window title color |
| `window.border` | Window border color |

### Glyph Slots

| Slot | Description |
|------|-------------|
| `checkbox.checked` | Checked checkbox glyph |
| `checkbox.unchecked` | Unchecked checkbox glyph |
| `radio.selected` | Selected radio glyph |
| `radio.unselected` | Unselected radio glyph |
| `scrollbar.track` | Scrollbar track character |
| `scrollbar.thumb` | Scrollbar thumb character |
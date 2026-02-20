# themes/black_white.py - Black and White Theme

Monochrome color scheme for classic terminal look.

---

## Theme: `black_white`

A monochrome black and white theme with inverted highlights.

### Colors

| Slot | Color |
|------|-------|
| `bg` | Black |
| `fg` | Light gray |
| `label.fg` | White |
| `button.bg` | Dark gray |
| `button.fg` | White |
| `button.focused.bg` | White (inverted) |
| `button.focused.fg` | Black |
| `input.bg` | Dark gray |
| `input.fg` | White |
| `input.focused.bg` | White (inverted) |
| `window.bg` | Black |
| `window.border` | Medium gray |
| `window.active.border` | White |

### Glyphs

| Glyph | Character |
|-------|-----------|
| `checkbox.checked` | `[+]` |
| `checkbox.unchecked` | `[ ]` |
| `radio.selected` | `(*)` |
| `scrollbar.thumb` | `▓` |
| `scrollbar.track` | `░` |
| `window.close` | `X` |

### Usage

```python
app = App(theme="black_white")
```

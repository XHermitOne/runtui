# themes/high_contrast.py - High Contrast Theme

High contrast accessibility color scheme.

---

## Theme: `high_contrast`

An accessibility-focused theme with maximum contrast using black, white, cyan, and yellow.

### Colors

| Slot | Color |
|------|-------|
| `bg` | Black |
| `fg` | White |
| `label.fg` | White |
| `button.bg` | White |
| `button.fg` | Black |
| `button.focused.bg` | Cyan |
| `button.pressed.bg` | Yellow |
| `input.bg` | Black |
| `input.fg` | White |
| `input.focused.bg` | Cyan |
| `input.cursor` | Black |
| `input.selection.bg` | Yellow |
| `window.bg` | Black |
| `window.border` | White |
| `window.active.border` | Cyan |
| `window.active.title.bg` | Cyan |
| `dialog.border` | Yellow |
| `menu.selected.bg` | Yellow |
| `menu.hotkey` | Cyan |
| `taskbar.active.bg` | Cyan |

### Glyphs

| Glyph | Character |
|-------|-----------|
| `checkbox.checked` | `[ X ]` |
| `checkbox.unchecked` | `[   ]` |
| `radio.selected` | `( @ )` |
| `scrollbar.thumb` | `█` |
| `scrollbar.track` | `░` |
| `window.close` | ` X ` |
| `window.maximize` | ` □ ` |
| `menu.arrow` | `>>` |
| `menu.separator` | `=` |
| `cursor.arrow` | `->` |
| `cursor.hand` | `H` |

### Usage

```python
app = App(theme="high_contrast")
```

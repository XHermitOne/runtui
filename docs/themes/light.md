# themes/light.py - Light Theme

Modern light color scheme (default).

---

## Theme: `light`

A modern light theme with dark text on light backgrounds and accent blue highlights.

### Colors

| Slot | Color |
|------|-------|
| `bg` | White (#ffffff) |
| `fg` | Dark gray (#1e1e1e) |
| `label.fg` | Dark gray |
| `button.bg` | Accent blue (#0078d4) |
| `button.fg` | White |
| `button.focused.bg` | Light blue accent |
| `button.pressed.bg` | Darker blue |
| `input.bg` | White |
| `input.fg` | Dark gray |
| `input.focused.bg` | Light yellow (#ffffe6) |
| `input.cursor` | Dark gray |
| `input.selection.bg` | Accent blue |
| `window.bg` | White |
| `window.border` | Light gray (#c8c8c8) |
| `window.active.border` | Accent blue |
| `window.active.title.bg` | Accent blue |
| `dialog.bg` | Surface gray (#f5f5f5) |
| `dialog.border` | Accent blue |
| `menu.bg` | Surface gray |
| `menu.selected.bg` | Accent blue |
| `menu.hotkey` | Red |
| `taskbar.bg` | Surface gray |
| `taskbar.active.bg` | Accent blue |

### Border Styles

| Element | Style |
|---------|-------|
| `window` | `ROUNDED` |
| `dialog` | `ROUNDED` |
| `container` | `SINGLE` |
| `input` | `SINGLE` |

### Glyphs

| Glyph | Character |
|-------|-----------|
| `checkbox.checked` | `[✓]` |
| `checkbox.unchecked` | `[ ]` |
| `radio.selected` | `(●)` |
| `radio.unselected` | `(○)` |
| `scrollbar.thumb` | `█` |
| `scrollbar.track` | `░` |
| `scrollbar.up` | `▲` |
| `scrollbar.down` | `▼` |
| `window.close` | `[×]` |
| `window.maximize` | `[□]` |
| `window.minimize` | `[_]` |
| `menu.arrow` | `›` |
| `dropdown.arrow` | `▾` |
| `cursor.arrow` | `▶` |
| `cursor.hand` | `☞` |
| `cursor.text` | `│` |

### Usage

```python
app = App(theme="light")
```

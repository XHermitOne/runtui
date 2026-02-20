# themes/github.py - GitHub Theme

GitHub-inspired light color scheme.

---

## Theme: `github`

A light theme based on GitHub's design language with accent blues and greens.

### Colors

| Slot | Color |
|------|-------|
| `bg` | Light gray (#f6f8fa) |
| `fg` | Dark gray (#24292f) |
| `label.fg` | Dark gray |
| `button.bg` | Green (#2da44e) |
| `button.fg` | White |
| `button.focused.bg` | Blue accent (#0969da) |
| `input.bg` | Light gray |
| `input.fg` | Dark gray |
| `input.cursor` | Blue accent |
| `input.selection.bg` | Light blue (#ddf4ff) |
| `window.bg` | White |
| `window.border` | Gray (#d0d7de) |
| `window.active.border` | Blue accent |

### Glyphs

| Glyph | Character |
|-------|-----------|
| `checkbox.checked` | `[x]` |
| `checkbox.unchecked` | `[ ]` |
| `radio.selected` | `(•)` |
| `scrollbar.thumb` | `│` |
| `scrollbar.track` | ` ` |
| `window.close` | `[×]` |
| `menu.arrow` | `→` |
| `dropdown.arrow` | `▼` |
| `cursor.arrow` | `➤` |
| `cursor.hand` | `👆` |

### Usage

```python
app = App(theme="github")
```

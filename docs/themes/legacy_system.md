# themes/legacy_system.py - Legacy System Theme

DOS/BIOS-era color scheme for nostalgic look.

---

## Theme: `legacy_system`

A nostalgic theme inspired by classic DOS and BIOS interfaces with cyan accents on blue and gray backgrounds.

### Colors

| Slot | Color |
|------|-------|
| `bg` | BIOS blue (#0000aa) |
| `fg` | BIOS gray (#aaaaaa) |
| `label.fg` | BIOS blue |
| `label.bg` | BIOS gray |
| `button.bg` | White |
| `button.fg` | Black |
| `button.focused.bg` | BIOS cyan (#00aaaa) |
| `button.pressed.bg` | BIOS blue |
| `input.bg` | BIOS blue |
| `input.fg` | White |
| `input.focused.bg` | BIOS blue |
| `input.focused.fg` | Yellow |
| `input.cursor` | Yellow |
| `window.bg` | BIOS gray |
| `window.border` | BIOS blue |
| `window.active.border` | White |
| `window.active.title.bg` | BIOS cyan |
| `dialog.bg` | BIOS gray |
| `dialog.border` | BIOS blue |
| `menu.bg` | BIOS gray |
| `menu.selected.bg` | BIOS cyan |
| `menu.hotkey` | BIOS red (#aa0000) |
| `taskbar.bg` | BIOS gray |
| `taskbar.active.bg` | BIOS cyan |

### Glyphs

| Glyph | Character |
|-------|-----------|
| `checkbox.checked` | `[■]` |
| `checkbox.unchecked` | `[ ]` |
| `radio.selected` | `(■)` |
| `scrollbar.thumb` | `░` |
| `scrollbar.track` | `│` |
| `window.close` | `[x]` |
| `menu.arrow` | `►` |
| `cursor.arrow` | `►` |
| `cursor.hand` | `»` |

### Usage

```python
app = App(theme="legacy_system")
```

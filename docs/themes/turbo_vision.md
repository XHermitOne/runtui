# themes/turbo_vision.py - Turbo Vision Theme

Classic Turbo Vision color scheme from the DOS era.

---

## Theme: `turbo_vision`

A nostalgic theme based on Borland Turbo Vision from the DOS era. Features classic blue desktop with cyan accents and gray dialogs.

### Characteristics

- Classic blue desktop background
- Cyan and yellow accents
- White text on blue for active elements
- Gray dialogs with double borders
- Green buttons and menu selections

### Colors

| Slot | Color |
|------|-------|
| `desktop.bg` | Blue (ANSI 4) |
| `desktop.fg` | Light blue (ANSI 12) |
| `window.bg` | Light gray (ANSI 7) |
| `window.fg` | Black |
| `window.border` | Light gray |
| `window.active.border` | White |
| `window.active.title.bg` | Light gray |
| `label.fg` | Black |
| `label.bg` | Light gray |
| `button.bg` | Green (ANSI 2) |
| `button.fg` | White |
| `button.focused.bg` | Cyan (ANSI 6) |
| `button.shadow` | Dark gray |
| `input.bg` | Cyan (ANSI 6) |
| `input.fg` | Blue (ANSI 4) |
| `input.focused.bg` | Blue |
| `input.focused.fg` | Yellow (ANSI 11) |
| `input.cursor` | White |
| `menu.bg` | Light gray |
| `menu.fg` | Black |
| `menu.selected.bg` | Green |
| `menu.hotkey` | Red |
| `checkbox.focused.bg` | Blue |
| `checkbox.focused.fg` | Yellow |
| `dialog.bg` | Light gray |
| `dialog.border` | White |
| `dialog.title` | White |
| `listbox.bg` | Cyan |
| `listbox.selected.bg` | Green |
| `calendar.bg` | Cyan |
| `calendar.today` | Yellow |
| `taskbar.bg` | Cyan |
| `taskbar.fg` | Black |
| `taskbar.active.bg` | Green |

### Border Styles

| Element | Style |
|---------|-------|
| `window` | `DOUBLE` |
| `dialog` | `DOUBLE` |
| `container` | `SINGLE` |
| `input` | `SINGLE` |

### Glyphs

| Glyph | Character |
|-------|-----------|
| `checkbox.checked` | `[X]` |
| `checkbox.unchecked` | `[ ]` |
| `radio.selected` | `(*)` |
| `radio.unselected` | `( )` |
| `scrollbar.thumb` | `█` |
| `scrollbar.track` | `░` |
| `scrollbar.up` | `▲` |
| `scrollbar.down` | `▼` |
| `window.close` | `[■]` |
| `window.maximize` | `[▲]` |
| `window.minimize` | `[▼]` |
| `menu.arrow` | `►` |
| `dropdown.arrow` | `▼` |
| `cursor.arrow` | `▶` |
| `cursor.hand` | `☞` |
| `cursor.text` | `│` |

### Usage

```python
app = App(theme="turbo_vision")
```

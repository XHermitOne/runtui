# themes/vscode.py - VS Code Theme

VS Code Dark inspired color scheme.

---

## Theme: `vscode`

A dark theme based on Visual Studio Code's default dark theme.

### Colors

| Slot | Color |
|------|-------|
| `bg` | Dark (#1e1e1e) |
| `fg` | Light gray (#cccccc) |
| `label.fg` | Light gray |
| `button.bg` | Dark blue (#0e639c) |
| `button.fg` | White |
| `button.focused.bg` | Blue accent (#007acc) |
| `input.bg` | Widget gray (#2d2d30) |
| `input.fg` | Light gray |
| `input.focused.bg` | Darker gray (#333333) |
| `input.cursor` | White |
| `input.selection.bg` | Selection blue (#264f78) |
| `window.bg` | Sidebar gray (#252526) |
| `window.border` | Border gray (#454545) |
| `window.active.border` | Blue accent |
| `dialog.bg` | Widget gray |
| `dialog.border` | Blue accent |
| `menu.bg` | Widget gray |
| `menu.selected.bg` | Blue accent |
| `menu.hotkey` | Orange (#ce9178) |
| `taskbar.bg` | Blue accent |
| `taskbar.active.bg` | Darker gray |

### Glyphs

| Glyph | Character |
|-------|-----------|
| `checkbox.checked` | `[✓]` |
| `checkbox.unchecked` | `[ ]` |
| `radio.selected` | `(●)` |
| `scrollbar.thumb` | ` ` |
| `scrollbar.track` | `░` |
| `window.close` | `[x]` |
| `window.maximize` | `[□]` |
| `menu.arrow` | `>` |
| `dropdown.arrow` | `v` |
| `cursor.arrow` | `▶` |
| `cursor.hand` | `👆` |

### Usage

```python
app = App(theme="vscode")
```

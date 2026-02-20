# keys.py - Key Constants and Modifiers

Key codes, modifiers, and mouse button/action enumerations.

---

## Enum: `Modifiers`

Keyboard modifier flags that can be combined.

```python
class Modifiers(enum.Flag):
    NONE = 0
    SHIFT = enum.auto()
    ALT = enum.auto()
    CTRL = enum.auto()
    META = enum.auto()
```

| Flag | Description |
|------|-------------|
| `NONE` | No modifiers |
| `SHIFT` | Shift key held |
| `ALT` | Alt/Option key held |
| `CTRL` | Control key held |
| `META` | Meta/Super/Windows key held |

---

## Enum: `Keys`

Named key constants for special keys.

```python
class Keys(enum.Enum):
```

### Special Keys

| Value | Description |
|-------|-------------|
| `UNKNOWN` | Unknown/unrecognized key |
| `ESCAPE` | Escape key |
| `ENTER` | Enter/Return key |
| `TAB` | Tab key |
| `BACKSPACE` | Backspace key |
| `DELETE` | Delete key |
| `INSERT` | Insert key |
| `SPACE` | Space bar |

### Navigation Keys

| Value | Description |
|-------|-------------|
| `UP` | Up arrow |
| `DOWN` | Down arrow |
| `LEFT` | Left arrow |
| `RIGHT` | Right arrow |
| `HOME` | Home key |
| `END` | End key |
| `PAGE_UP` | Page Up key |
| `PAGE_DOWN` | Page Down key |

### Function Keys

| Value | Description |
|-------|-------------|
| `F1` through `F12` | Function keys F1-F12 |
| `CHAR` | Placeholder for printable characters (actual char is in `KeyEvent.char`) |

---

## Enum: `MouseButton`

Mouse button identifiers.

```python
class MouseButton(enum.Enum):
```

| Value | Description |
|-------|-------------|
| `NONE` | No button |
| `LEFT` | Left mouse button |
| `MIDDLE` | Middle mouse button |
| `RIGHT` | Right mouse button |
| `SCROLL_UP` | Scroll wheel up |
| `SCROLL_DOWN` | Scroll wheel down |

---

## Enum: `MouseAction`

Mouse action types.

```python
class MouseAction(enum.Enum):
```

| Value | Description |
|-------|-------------|
| `PRESS` | Button pressed down |
| `RELEASE` | Button released |
| `MOVE` | Mouse moved |
| `DRAG` | Mouse moved while button held |

---

## Internal Constants

### `_CSI_KEY_MAP`

Maps CSI sequence endings to `Keys` values for arrow keys, home, end, etc.

### `_CSI_TILDE_MAP`

Maps CSI tilde parameters to `Keys` values for function keys and navigation.

### `_SS3_KEY_MAP`

Maps SS3 sequences to `Keys` values for function keys F1-F4, home, end.

---

## Functions

### `decode_modifiers_from_param`

```python
def decode_modifiers_from_param(param: int) -> Modifiers
```

Decode xterm modifier parameter to `Modifiers` flags.

In xterm escape sequences, the modifier parameter is encoded as (param - 1) where:
- Bit 0 = Shift
- Bit 1 = Alt
- Bit 2 = Ctrl
- Bit 3 = Meta

**Parameters:**
- `param` (`int`): The xterm modifier parameter

**Returns:** `Modifiers` - The decoded modifier flags

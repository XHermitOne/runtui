# key_encode.py - Key Encoding

Encode runtui KeyEvents back to raw terminal byte sequences.

This is the inverse of `UnixBackend.decode_input()`: given a KeyEvent, produce the bytes that a real terminal would send, so keystrokes can be forwarded to a child process running in a PTY.

---

## Functions

### `encode_key`

```python
def encode_key(event: KeyEvent) -> bytes
```

Convert a KeyEvent into the raw bytes a terminal would send.

Handles:
- Regular characters (UTF-8 encoded)
- Ctrl+letter combinations (Ctrl+A = 0x01, etc.)
- Alt+key combinations (ESC prefix)
- Special keys (Enter, Tab, Backspace, Escape)
- Arrow and navigation keys (CSI sequences)
- Function keys (F1-F12)
- Modified keys (Shift/Alt/Ctrl + special keys)

**Parameters:**
- `event` (`KeyEvent`): The key event to encode

**Returns:** `bytes` - The raw terminal byte sequence

---

## Internal Constants

### `_SIMPLE_KEY_MAP`

Keys that map to simple fixed byte sequences:

| Key | Bytes |
|-----|-------|
| `ENTER` | `b"\r"` |
| `TAB` | `b"\t"` |
| `BACKSPACE` | `b"\x7f"` |
| `ESCAPE` | `b"\x1b"` |

### `_CSI_KEY_MAP`

Keys that use CSI (Control Sequence Introducer) sequences:

| Key | Sequence |
|-----|----------|
| `UP` | `ESC[A` |
| `DOWN` | `ESC[B` |
| `RIGHT` | `ESC[C` |
| `LEFT` | `ESC[D` |
| `HOME` | `ESC[H` |
| `END` | `ESC[F` |
| `INSERT` | `ESC[2~` |
| `DELETE` | `ESC[3~` |
| `PAGE_UP` | `ESC[5~` |
| `PAGE_DOWN` | `ESC[6~` |
| `F1` through `F12` | `ESC[11~` through `ESC[24~` |

---

## Helper Functions

### `_modifier_param`

```python
def _modifier_param(mods: Modifiers) -> int
```

Encode modifiers as an xterm parameter (1 + bitmask).

| Bit | Modifier |
|-----|----------|
| 0 | Shift |
| 1 | Alt |
| 2 | Ctrl |
| 3 | Meta |

**Parameters:**
- `mods` (`Modifiers`): Modifier flags

**Returns:** `int` - The xterm parameter value
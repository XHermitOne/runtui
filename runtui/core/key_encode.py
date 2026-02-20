"""Encode runtui KeyEvents back to raw terminal byte sequences.

This is the inverse of UnixBackend.decode_input(): given a KeyEvent,
produce the bytes that a real terminal would send so we can forward
keystrokes to a child process running in a PTY.
"""

from __future__ import annotations

from ..core.event import KeyEvent
from ..core.keys import Keys, Modifiers


def encode_key(event: KeyEvent) -> bytes:
    """Convert a KeyEvent into the raw bytes a terminal would send."""
    key = event.key
    mods = event.modifiers
    char = event.char

    # --- Ctrl+<letter> ---
    if key == Keys.CHAR and char and Modifiers.CTRL in mods:
        # Ctrl+A=0x01 .. Ctrl+Z=0x1A
        c = char.lower()
        if "a" <= c <= "z":
            return bytes([ord(c) - ord("a") + 1])
        # Ctrl+[ = ESC, Ctrl+\ = 0x1C, etc.
        if c == "[":
            return b"\x1b"
        if c == "\\":
            return b"\x1c"
        if c == "]":
            return b"\x1d"
        if c == "^":
            return b"\x1e"
        if c == "_":
            return b"\x1f"
        # Fall through for unknown ctrl combos
        return char.encode("utf-8")

    # --- Alt+<key> ---
    if key == Keys.CHAR and char and Modifiers.ALT in mods and Modifiers.CTRL not in mods:
        return b"\x1b" + char.encode("utf-8")

    # --- Simple named keys ---
    simple = _SIMPLE_KEY_MAP.get(key)
    if simple is not None:
        return simple

    # --- Arrow / nav keys with possible modifiers ---
    csi = _CSI_KEY_MAP.get(key)
    if csi is not None:
        suffix, param_code = csi
        if isinstance(suffix, int):
            # tilde-style: ESC [ N ~  or  ESC [ N ; mod ~
            mod_param = _modifier_param(mods)
            if mod_param > 1:
                return f"\x1b[{suffix};{mod_param}~".encode("ascii")
            return f"\x1b[{suffix}~".encode("ascii")
        else:
            # letter-style: ESC [ A  or  ESC [ 1 ; mod A
            mod_param = _modifier_param(mods)
            if mod_param > 1:
                return f"\x1b[1;{mod_param}{suffix}".encode("ascii")
            return f"\x1b[{suffix}".encode("ascii")

    # --- Regular character ---
    if key == Keys.CHAR and char:
        return char.encode("utf-8")

    # --- Space ---
    if key == Keys.SPACE:
        if Modifiers.CTRL in mods:
            return b"\x00"
        return b" "

    return b""


def _modifier_param(mods: Modifiers) -> int:
    """Encode modifiers as xterm parameter (1 + bitmask)."""
    bits = 0
    if Modifiers.SHIFT in mods:
        bits |= 1
    if Modifiers.ALT in mods:
        bits |= 2
    if Modifiers.CTRL in mods:
        bits |= 4
    if Modifiers.META in mods:
        bits |= 8
    return 1 + bits


# Keys that map to simple fixed byte sequences
_SIMPLE_KEY_MAP: dict[Keys, bytes] = {
    Keys.ENTER: b"\r",
    Keys.TAB: b"\t",
    Keys.BACKSPACE: b"\x7f",
    Keys.ESCAPE: b"\x1b",
}

# Keys that use CSI sequences: key -> (suffix, param_code)
# suffix is either a string letter (like "A") or an int for tilde-style
_CSI_KEY_MAP: dict[Keys, tuple[str | int, int]] = {
    Keys.UP:        ("A", 0),
    Keys.DOWN:      ("B", 0),
    Keys.RIGHT:     ("C", 0),
    Keys.LEFT:      ("D", 0),
    Keys.HOME:      ("H", 0),
    Keys.END:       ("F", 0),
    Keys.INSERT:    (2, 0),
    Keys.DELETE:    (3, 0),
    Keys.PAGE_UP:   (5, 0),
    Keys.PAGE_DOWN: (6, 0),
    Keys.F1:        (11, 0),
    Keys.F2:        (12, 0),
    Keys.F3:        (13, 0),
    Keys.F4:        (14, 0),
    Keys.F5:        (15, 0),
    Keys.F6:        (17, 0),
    Keys.F7:        (18, 0),
    Keys.F8:        (19, 0),
    Keys.F9:        (20, 0),
    Keys.F10:       (21, 0),
    Keys.F11:       (23, 0),
    Keys.F12:       (24, 0),
}

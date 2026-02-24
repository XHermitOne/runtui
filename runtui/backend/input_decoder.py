"""Shared ANSI input decoder used by runtui backends."""

from __future__ import annotations

from typing import List, Tuple

from ..core.event import Event, KeyEvent, MouseEvent
from ..core.keys import (
    Keys,
    Modifiers,
    MouseAction,
    MouseButton,
    _CSI_KEY_MAP,
    _CSI_TILDE_MAP,
    _SS3_KEY_MAP,
    decode_modifiers_from_param,
)


class AnsiInputDecoder:
    """Stateful parser for ANSI terminal input sequences."""

    def __init__(self) -> None:
        self._input_buffer = b""

    def feed(self, raw: bytes) -> list[Event]:
        """Decode raw bytes into Event objects."""
        if not raw:
            return []

        events: List[Event] = []
        self._input_buffer += raw
        buf = self._input_buffer
        i = 0
        while i < len(buf):
            byte = buf[i]
            if byte == 0x1B:
                consumed, event = self._parse_escape(buf, i)
                if consumed > 0:
                    if event:
                        events.append(event)
                    i += consumed
                    continue
                self._input_buffer = buf[i:]
                return events
            if byte < 0x20:
                event = self._decode_control(byte)
                if event:
                    events.append(event)
                i += 1
                continue
            if byte == 0x7F:
                events.append(KeyEvent(key=Keys.BACKSPACE))
                i += 1
                continue
            consumed, char = self._decode_utf8(buf, i)
            if consumed > 0:
                if char:
                    events.append(KeyEvent(key=Keys.CHAR, char=char))
                i += consumed
            else:
                self._input_buffer = buf[i:]
                return events

        self._input_buffer = b""
        return events

    # --- parsing helpers -------------------------------------------------

    def _parse_escape(self, buf: bytes, start: int) -> tuple[int, Event | None]:
        if start + 1 >= len(buf):
            return (0, None)
        next_byte = buf[start + 1]
        if next_byte == ord("["):
            return self._parse_csi(buf, start)
        if next_byte == ord("O"):
            return self._parse_ss3(buf, start)
        if 0x20 <= next_byte < 0x7F:
            char = chr(next_byte)
            return (2, KeyEvent(key=Keys.CHAR, char=char, modifiers=Modifiers.ALT))
        return (1, KeyEvent(key=Keys.ESCAPE))

    def _parse_csi(self, buf: bytes, start: int) -> tuple[int, Event | None]:
        i = start + 2
        length = len(buf)
        if i >= length:
            return (0, None)
        if buf[i:i + 1] == b"<":
            return self._parse_sgr_mouse(buf, start)
        params_start = i
        while i < length and 0x30 <= buf[i] <= 0x3F:
            i += 1
        if i >= length:
            return (0, None)
        params_str = buf[params_start:i].decode("ascii", errors="ignore")
        final = chr(buf[i])
        consumed = i - start + 1
        params = [int(p) if p else 0 for p in params_str.split(";")] if params_str else []
        if final in _CSI_KEY_MAP:
            key = _CSI_KEY_MAP[final]
            mods = Modifiers.NONE
            if len(params) >= 2:
                mods = decode_modifiers_from_param(params[1])
            if final == "Z":
                mods |= Modifiers.SHIFT
            return (consumed, KeyEvent(key=key, modifiers=mods))
        if final == "~" and params:
            key = _CSI_TILDE_MAP.get(params[0])
            if key:
                mods = Modifiers.NONE
                if len(params) >= 2:
                    mods = decode_modifiers_from_param(params[1])
                return (consumed, KeyEvent(key=key, modifiers=mods))
        return (consumed, None)

    def _parse_ss3(self, buf: bytes, start: int) -> tuple[int, Event | None]:
        i = start + 2
        if i >= len(buf):
            return (0, None)
        final = chr(buf[i])
        key = _SS3_KEY_MAP.get(final)
        if key:
            return (3, KeyEvent(key=key))
        return (3, None)

    def _parse_sgr_mouse(self, buf: bytes, start: int) -> tuple[int, Event | None]:
        i = start + 3
        length = len(buf)
        params_start = i
        while i < length and buf[i] not in (ord("M"), ord("m")):
            i += 1
        if i >= length:
            return (0, None)
        params_str = buf[params_start:i].decode("ascii", errors="ignore")
        release = buf[i] == ord("m")
        consumed = i - start + 1
        parts = params_str.split(";")
        if len(parts) != 3:
            return (consumed, None)
        try:
            cb = int(parts[0])
            px = int(parts[1]) - 1
            py = int(parts[2]) - 1
        except ValueError:
            return (consumed, None)
        mods = Modifiers.NONE
        if cb & 4:
            mods |= Modifiers.SHIFT
        if cb & 8:
            mods |= Modifiers.ALT
        if cb & 16:
            mods |= Modifiers.CTRL
        button_bits = cb & 0x43
        is_motion = bool(cb & 32)
        if button_bits == 64:
            return (consumed, MouseEvent(
                x=px, y=py, button=MouseButton.SCROLL_UP,
                action=MouseAction.PRESS, modifiers=mods,
            ))
        if button_bits == 65:
            return (consumed, MouseEvent(
                x=px, y=py, button=MouseButton.SCROLL_DOWN,
                action=MouseAction.PRESS, modifiers=mods,
            ))
        btn = MouseButton.NONE
        if button_bits == 0:
            btn = MouseButton.LEFT
        elif button_bits == 1:
            btn = MouseButton.MIDDLE
        elif button_bits == 2:
            btn = MouseButton.RIGHT
        if release:
            action = MouseAction.RELEASE
        elif is_motion:
            action = MouseAction.DRAG if btn != MouseButton.NONE else MouseAction.MOVE
        else:
            action = MouseAction.PRESS
        return (consumed, MouseEvent(
            x=px, y=py, button=btn, action=action, modifiers=mods,
        ))

    def _decode_control(self, byte: int) -> Event | None:
        if byte == 0x0D:
            return KeyEvent(key=Keys.ENTER)
        if byte == 0x09:
            return KeyEvent(key=Keys.TAB)
        if byte == 0x08:
            return KeyEvent(key=Keys.BACKSPACE)
        if byte == 0x00:
            return KeyEvent(key=Keys.SPACE, modifiers=Modifiers.CTRL)
        if 0x01 <= byte <= 0x1A:
            char = chr(byte + 0x60)
            return KeyEvent(key=Keys.CHAR, char=char, modifiers=Modifiers.CTRL)
        return None

    def _decode_utf8(self, buf: bytes, start: int) -> Tuple[int, str]:
        b0 = buf[start]
        if b0 < 0x80:
            return (1, chr(b0))
        if b0 < 0xC0:
            return (1, "")
        if b0 < 0xE0:
            need = 2
        elif b0 < 0xF0:
            need = 3
        else:
            need = 4
        if start + need > len(buf):
            return (0, "")
        try:
            char = buf[start:start + need].decode("utf-8")
            return (need, char)
        except UnicodeDecodeError:
            return (1, "")

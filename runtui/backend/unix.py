"""Unix (Linux/macOS) terminal backend using ANSI escape sequences."""

from __future__ import annotations

import os
import re
import select
import signal
import sys
import termios
import tty
from typing import Any, Callable

from ..core.event import (
    Event,
    KeyEvent,
    MouseEvent,
    ResizeEvent,
)
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
from ..core.types import ColorDepth
from .base import Backend


class UnixBackend(Backend):
    """Terminal backend for Linux and macOS."""

    def __init__(self) -> None:
        self._original_termios: list[Any] | None = None
        self._resize_pending = False
        self._old_sigwinch: Any = None
        self._input_buffer = b""
        self._pty_callbacks: dict[int, Callable[[bytes], None]] = {}

    def init(self) -> None:
        fd = sys.stdin.fileno()
        self._original_termios = termios.tcgetattr(fd)
        tty.setraw(fd, termios.TCSANOW)
        self.enter_alternate_screen()
        self.set_cursor_visible(False)
        self.enable_mouse()
        self.clear_screen()
        self.flush()
        # Handle SIGWINCH for terminal resize
        self._old_sigwinch = signal.getsignal(signal.SIGWINCH)
        signal.signal(signal.SIGWINCH, self._handle_sigwinch)

    def shutdown(self) -> None:
        self.disable_mouse()
        self.set_cursor_visible(True)
        self.reset_attributes()
        self.leave_alternate_screen()
        self.flush()
        if self._original_termios is not None:
            fd = sys.stdin.fileno()
            termios.tcsetattr(fd, termios.TCSANOW, self._original_termios)
        if self._old_sigwinch is not None:
            signal.signal(signal.SIGWINCH, self._old_sigwinch)

    def get_size(self) -> tuple[int, int]:
        try:
            size = os.get_terminal_size(sys.stdout.fileno())
            return (size.columns, size.lines)
        except OSError:
            return (80, 24)

    def read_input(self) -> bytes:
        fd = sys.stdin.fileno()
        # Build the list of fds to poll: stdin + any registered PTY masters
        watch_fds = [fd] + list(self._pty_callbacks.keys())
        rlist, _, _ = select.select(watch_fds, [], [], 0.01)

        # Service any PTY fds that have data ready
        for ready_fd in rlist:
            if ready_fd != fd and ready_fd in self._pty_callbacks:
                try:
                    data = os.read(ready_fd, 65536)
                    if data:
                        self._pty_callbacks[ready_fd](data)
                except OSError:
                    # Child probably died — invoke callback with empty
                    # to let the widget detect the EOF on its next read
                    cb = self._pty_callbacks.get(ready_fd)
                    if cb:
                        try:
                            cb(b"")
                        except Exception:
                            pass

        if fd not in rlist:
            # No stdin data — check for pending resize
            if self._resize_pending:
                self._resize_pending = False
                return b"\x1b[RESIZE]"  # Synthetic marker
            return b""
        data = os.read(fd, 4096)
        return data

    def register_pty_fd(self, fd: int, callback: Callable[[bytes], None]) -> None:
        """Register a PTY master fd to be polled in the select() loop."""
        self._pty_callbacks[fd] = callback

    def unregister_pty_fd(self, fd: int) -> None:
        """Remove a PTY fd from the select() loop."""
        self._pty_callbacks.pop(fd, None)

    def decode_input(self, raw: bytes) -> list[Event]:
        if not raw:
            return []

        # Check for synthetic resize marker
        if raw == b"\x1b[RESIZE]":
            cols, rows = self.get_size()
            return [ResizeEvent(width=cols, height=rows)]

        events: list[Event] = []
        self._input_buffer += raw
        buf = self._input_buffer

        i = 0
        while i < len(buf):
            # ESC sequence
            if buf[i:i + 1] == b"\x1b":
                consumed, event = self._parse_escape(buf, i)
                if consumed > 0:
                    if event:
                        events.append(event)
                    i += consumed
                else:
                    # Incomplete sequence, keep buffer
                    self._input_buffer = buf[i:]
                    return events
            # Ctrl+key (0x01-0x1A except 0x1B=ESC, 0x09=TAB, 0x0D=ENTER, 0x08/0x7F=BS)
            elif buf[i] < 0x20:
                event = self._decode_control(buf[i])
                if event:
                    events.append(event)
                i += 1
            elif buf[i] == 0x7F:
                events.append(KeyEvent(key=Keys.BACKSPACE))
                i += 1
            else:
                # Regular UTF-8 character
                consumed, char = self._decode_utf8(buf, i)
                if consumed > 0:
                    events.append(KeyEvent(key=Keys.CHAR, char=char))
                    i += consumed
                else:
                    # Incomplete UTF-8, keep buffer
                    self._input_buffer = buf[i:]
                    return events

        self._input_buffer = b""
        return events

    def _parse_escape(self, buf: bytes, start: int) -> tuple[int, Event | None]:
        """Parse escape sequence starting at buf[start]. Returns (bytes_consumed, event)."""
        length = len(buf)
        if start + 1 >= length:
            # Could be just ESC or incomplete sequence
            # Wait a bit for more data
            return (0, None)

        next_byte = buf[start + 1]

        # CSI sequence: ESC [
        if next_byte == ord("["):
            return self._parse_csi(buf, start)

        # SS3 sequence: ESC O
        if next_byte == ord("O"):
            return self._parse_ss3(buf, start)

        # Alt+key: ESC followed by a character
        if 0x20 <= next_byte < 0x7F:
            char = chr(next_byte)
            return (2, KeyEvent(key=Keys.CHAR, char=char, modifiers=Modifiers.ALT))

        # Just ESC
        return (1, KeyEvent(key=Keys.ESCAPE))

    def _parse_csi(self, buf: bytes, start: int) -> tuple[int, Event | None]:
        """Parse CSI sequence: ESC [ ... """
        i = start + 2
        length = len(buf)

        if i >= length:
            return (0, None)

        # Check for SGR mouse: ESC [ < ...
        if buf[i:i + 1] == b"<":
            return self._parse_sgr_mouse(buf, start)

        # Collect parameter bytes (0x30-0x3F)
        params_start = i
        while i < length and 0x30 <= buf[i] <= 0x3F:
            i += 1
        if i >= length:
            return (0, None)

        params_str = buf[params_start:i].decode("ascii", errors="ignore")

        # Final byte
        final = chr(buf[i])
        consumed = i - start + 1

        # Parse parameters
        params = [int(p) if p else 0 for p in params_str.split(";")] if params_str else []

        # Letter finishers
        if final in _CSI_KEY_MAP:
            key = _CSI_KEY_MAP[final]
            mods = Modifiers.NONE
            if len(params) >= 2:
                mods = decode_modifiers_from_param(params[1])
            if final == "Z":
                mods |= Modifiers.SHIFT
            return (consumed, KeyEvent(key=key, modifiers=mods))

        # Tilde finishers: ESC [ N ~
        if final == "~" and params:
            key = _CSI_TILDE_MAP.get(params[0])
            if key:
                mods = Modifiers.NONE
                if len(params) >= 2:
                    mods = decode_modifiers_from_param(params[1])
                return (consumed, KeyEvent(key=key, modifiers=mods))

        return (consumed, None)

    def _parse_ss3(self, buf: bytes, start: int) -> tuple[int, Event | None]:
        """Parse SS3 sequence: ESC O ..."""
        i = start + 2
        if i >= len(buf):
            return (0, None)
        final = chr(buf[i])
        key = _SS3_KEY_MAP.get(final)
        if key:
            return (3, KeyEvent(key=key))
        return (3, None)

    def _parse_sgr_mouse(self, buf: bytes, start: int) -> tuple[int, Event | None]:
        """Parse SGR mouse: ESC [ < Pb ; Px ; Py [Mm]"""
        i = start + 3  # skip ESC [ <
        length = len(buf)

        # Collect until M or m
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
            px = int(parts[1]) - 1  # 1-based to 0-based
            py = int(parts[2]) - 1
        except ValueError:
            return (consumed, None)

        # Decode button and modifiers from cb
        mods = Modifiers.NONE
        if cb & 4:
            mods |= Modifiers.SHIFT
        if cb & 8:
            mods |= Modifiers.ALT
        if cb & 16:
            mods |= Modifiers.CTRL

        button_bits = cb & 0x43  # bits 0,1 and 6
        is_motion = bool(cb & 32)

        if button_bits == 64:
            return (consumed, MouseEvent(
                x=px, y=py, button=MouseButton.SCROLL_UP,
                action=MouseAction.PRESS, modifiers=mods,
            ))
        elif button_bits == 65:
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
        elif button_bits == 3:
            btn = MouseButton.NONE

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
        """Decode control byte (0x00-0x1F)."""
        if byte == 0x0D:  # CR -> Enter
            return KeyEvent(key=Keys.ENTER)
        elif byte == 0x09:  # HT -> Tab
            return KeyEvent(key=Keys.TAB)
        elif byte == 0x08:  # BS -> Backspace
            return KeyEvent(key=Keys.BACKSPACE)
        elif byte == 0x00:  # Ctrl+Space
            return KeyEvent(key=Keys.SPACE, modifiers=Modifiers.CTRL)
        elif 0x01 <= byte <= 0x1A:
            # Ctrl+A through Ctrl+Z
            char = chr(byte + 0x60)  # 0x01 -> 'a'
            return KeyEvent(key=Keys.CHAR, char=char, modifiers=Modifiers.CTRL)
        return None

    def _decode_utf8(self, buf: bytes, start: int) -> tuple[int, str]:
        """Decode a single UTF-8 character. Returns (bytes_consumed, char)."""
        b0 = buf[start]
        if b0 < 0x80:
            return (1, chr(b0))
        elif b0 < 0xC0:
            return (1, "")  # Invalid continuation byte
        elif b0 < 0xE0:
            need = 2
        elif b0 < 0xF0:
            need = 3
        else:
            need = 4

        if start + need > len(buf):
            return (0, "")  # Incomplete

        try:
            char = buf[start:start + need].decode("utf-8")
            return (need, char)
        except UnicodeDecodeError:
            return (1, "")

    def write(self, data: str) -> None:
        sys.stdout.buffer.write(data.encode("utf-8"))

    def flush(self) -> None:
        sys.stdout.buffer.flush()

    def set_cursor_position(self, x: int, y: int) -> None:
        # ANSI is 1-based
        self.write(f"\x1b[{y + 1};{x + 1}H")

    def set_cursor_visible(self, visible: bool) -> None:
        if visible:
            self.write("\x1b[?25h")
        else:
            self.write("\x1b[?25l")

    def color_support(self) -> ColorDepth:
        term = os.environ.get("TERM", "")
        colorterm = os.environ.get("COLORTERM", "")
        if colorterm in ("truecolor", "24bit"):
            return ColorDepth.TRUE_COLOR
        if "256color" in term:
            return ColorDepth.COLORS_256
        if term in ("xterm", "screen", "tmux", "rxvt"):
            return ColorDepth.COLORS_256
        return ColorDepth.COLORS_16

    def _handle_sigwinch(self, signum: int, frame: Any) -> None:
        self._resize_pending = True

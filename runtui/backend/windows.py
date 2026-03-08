"""Windows terminal backend using Win32 Console API."""

from __future__ import annotations

import os
import sys
from typing import Any

from ..core.event import Event, ResizeEvent
from ..core.types import ColorDepth
from .base import Backend
from .input_decoder import AnsiInputDecoder


class WindowsBackend(Backend):
    """Terminal backend for Windows.

    Uses VT100 escape sequences via Windows Terminal / ConEmu / modern cmd.exe.
    Falls back to Win32 Console API for older terminals.
    """

    def __init__(self) -> None:
        self._original_mode_in: int = 0
        self._original_mode_out: int = 0
        self._decoder = AnsiInputDecoder()
        self._kernel32: Any = None
        self._use_vt: bool = False
        self._pending_resize = False
        self._cached_cols = 0
        self._cached_rows = 0

    def init(self) -> None:
        try:
            import ctypes
            import ctypes.wintypes
            self._kernel32 = ctypes.windll.kernel32  # type: ignore

            # Get handles
            stdin_h = self._kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
            stdout_h = self._kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE

            # Save original modes
            mode_in = ctypes.wintypes.DWORD()
            mode_out = ctypes.wintypes.DWORD()
            self._kernel32.GetConsoleMode(stdin_h, ctypes.byref(mode_in))
            self._kernel32.GetConsoleMode(stdout_h, ctypes.byref(mode_out))
            self._original_mode_in = mode_in.value
            self._original_mode_out = mode_out.value

            # Enable VT processing
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200
            ENABLE_MOUSE_INPUT = 0x0010
            ENABLE_WINDOW_INPUT = 0x0008

            new_mode_out = self._original_mode_out | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            self._kernel32.SetConsoleMode(stdout_h, new_mode_out)

            # Set input mode: enable VT input, mouse, window events
            ENABLE_LINE_INPUT = 0x0002
            ENABLE_ECHO_INPUT = 0x0004
            ENABLE_PROCESSED_INPUT = 0x0001
            new_mode_in = (
                ENABLE_VIRTUAL_TERMINAL_INPUT
                | ENABLE_MOUSE_INPUT
                | ENABLE_WINDOW_INPUT
            )
            self._kernel32.SetConsoleMode(stdin_h, new_mode_in)
            self._use_vt = True

            # Set UTF-8 code page
            self._kernel32.SetConsoleOutputCP(65001)
            self._kernel32.SetConsoleCP(65001)

        except (ImportError, AttributeError, OSError):
            # Fallback: just use ANSI sequences and hope for the best
            self._use_vt = True

        self.enter_alternate_screen()
        self.set_cursor_visible(False)
        self.enable_mouse()
        self.clear_screen()
        self.flush()
        cols, rows = self.get_size()
        self._cached_cols = cols
        self._cached_rows = rows

    def shutdown(self) -> None:
        self.disable_mouse()
        self.set_cursor_visible(True)
        self.reset_attributes()
        self.leave_alternate_screen()
        self.flush()

        if self._kernel32:
            try:
                stdin_h = self._kernel32.GetStdHandle(-10)
                stdout_h = self._kernel32.GetStdHandle(-11)
                self._kernel32.SetConsoleMode(stdin_h, self._original_mode_in)
                self._kernel32.SetConsoleMode(stdout_h, self._original_mode_out)
            except OSError:
                pass

    def get_size(self) -> tuple[int, int]:
        try:
            size = os.get_terminal_size()
            return (size.columns, size.lines)
        except OSError:
            return (80, 24)

    def read_input(self) -> bytes:
        """Read input using msvcrt for non-blocking key detection."""
        data = b""
        try:
            import msvcrt
            while msvcrt.kbhit():
                data += msvcrt.getch()
        except ImportError:
            # Fallback for environments without msvcrt
            import select
            try:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
                if rlist:
                    data = sys.stdin.buffer.read1(4096)  # type: ignore
            except (OSError, AttributeError):
                pass

        self._poll_resize()
        if not data and self._pending_resize:
            self._pending_resize = False
            return b"\x1b[RESIZE]"
        return data

    def decode_input(self, raw: bytes) -> list[Event]:
        """Decode input -- delegate to the same ANSI parser as Unix backend."""
        if not raw:
            return []

        if raw == b"\x1b[RESIZE]":
            cols, rows = self.get_size()
            self._cached_cols = cols
            self._cached_rows = rows
            return [ResizeEvent(width=cols, height=rows)]

        # Windows Terminal sends the same ANSI sequences as xterm
        return self._decoder.feed(raw)

    def write(self, data: str) -> None:
        sys.stdout.buffer.write(data.encode("utf-8", errors="replace"))

    def flush(self) -> None:
        sys.stdout.buffer.flush()

    def set_cursor_position(self, x: int, y: int) -> None:
        self.write(f"\x1b[{y + 1};{x + 1}H")

    def set_cursor_visible(self, visible: bool) -> None:
        self.write("\x1b[?25h" if visible else "\x1b[?25l")

    def color_support(self) -> ColorDepth:
        # Windows Terminal supports true color
        wt = os.environ.get("WT_SESSION", "")
        colorterm = os.environ.get("COLORTERM", "")
        if wt or colorterm in ("truecolor", "24bit"):
            return ColorDepth.TRUE_COLOR
        # ConEmu
        if os.environ.get("ConEmuANSI", "") == "ON":
            return ColorDepth.TRUE_COLOR
        return ColorDepth.COLORS_256

    def _poll_resize(self) -> None:
        try:
            size = os.get_terminal_size()
        except OSError:
            return
        cols, rows = size.columns, size.lines
        if cols != self._cached_cols or rows != self._cached_rows:
            self._cached_cols = cols
            self._cached_rows = rows
            self._pending_resize = True

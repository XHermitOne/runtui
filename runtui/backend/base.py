"""Abstract backend interface for terminal I/O."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from ..core.event import Event
from ..core.types import ColorDepth


class Backend(ABC):
    """Abstract interface for terminal backends."""

    @abstractmethod
    def init(self) -> None:
        """Enter raw mode, alternate screen, enable mouse tracking."""

    @abstractmethod
    def shutdown(self) -> None:
        """Restore terminal to original state."""

    @abstractmethod
    def get_size(self) -> tuple[int, int]:
        """Return (columns, rows)."""

    @abstractmethod
    def read_input(self) -> bytes:
        """Read available raw bytes from terminal input (non-blocking).
        Returns empty bytes if nothing available."""

    @abstractmethod
    def decode_input(self, raw: bytes) -> list[Event]:
        """Parse raw bytes into Event objects."""

    @abstractmethod
    def write(self, data: str) -> None:
        """Write string data (including escape sequences) to terminal."""

    @abstractmethod
    def flush(self) -> None:
        """Flush output buffer to terminal."""

    @abstractmethod
    def set_cursor_position(self, x: int, y: int) -> None:
        """Move cursor to (x, y) where (0,0) is top-left."""

    @abstractmethod
    def set_cursor_visible(self, visible: bool) -> None:
        """Show or hide the hardware cursor."""

    @abstractmethod
    def color_support(self) -> ColorDepth:
        """Detect and return the terminal's color depth."""

    # --- PTY file descriptor registration (for embedded terminals) ---

    def register_pty_fd(self, fd: int, callback: Callable[[bytes], None]) -> None:
        """Register a PTY master fd to be polled alongside stdin.

        When data is available on *fd*, the backend reads it and invokes
        *callback(data)*.  The default implementation is a no-op (Windows).
        """

    def unregister_pty_fd(self, fd: int) -> None:
        """Remove a previously registered PTY fd."""

    # --- Standard terminal escape helpers ---

    def enter_alternate_screen(self) -> None:
        self.write("\x1b[?1049h")

    def leave_alternate_screen(self) -> None:
        self.write("\x1b[?1049l")

    def enable_mouse(self) -> None:
        # Enable SGR any-event mouse tracking
        self.write("\x1b[?1003h")  # Any-event tracking
        self.write("\x1b[?1006h")  # SGR extended mode

    def disable_mouse(self) -> None:
        self.write("\x1b[?1006l")
        self.write("\x1b[?1003l")

    def clear_screen(self) -> None:
        self.write("\x1b[2J")

    def reset_attributes(self) -> None:
        self.write("\x1b[0m")

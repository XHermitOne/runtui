"""PTY-based terminal emulator widget with full VT100 support.

Spawns a child process inside a real pseudo-terminal (PTY) and uses
the ``pyte`` library to parse VT100/xterm escape sequences into a
screen grid that is rendered via the runtui Painter.

Features:
  - Interactive programs (vim, htop, bash) work correctly
  - Full ANSI color support (16, 256, and 24-bit true color)
  - Non-blocking I/O — PTY master fd is polled via the backend's select()
  - Scrollback history via pyte.HistoryScreen
  - TIOCSWINSZ resize notification to child on widget resize
"""

from __future__ import annotations

import os
import platform
import subprocess
import threading
import time

import pyte

from ..core.event import KeyEvent, MouseEvent
from ..core.key_encode import encode_key
from ..core.keys import Keys, Modifiers, MouseAction as MA, MouseButton
from ..core.pty_process import PtyProcess
from ..core.types import Attrs, Color, Rect, Size
from ..rendering.painter import Painter
from ..backend.base import Backend
from .base import Widget


# ---------------------------------------------------------------------------
#  pyte color name → runtui Color
# ---------------------------------------------------------------------------

_PYTE_NAMED_COLORS: dict[str, Color] = {
    "black":          Color.from_index(0),
    "red":            Color.from_index(1),
    "green":          Color.from_index(2),
    "brown":          Color.from_index(3),
    "blue":           Color.from_index(4),
    "magenta":        Color.from_index(5),
    "cyan":           Color.from_index(6),
    "white":          Color.from_index(7),
    "brightblack":    Color.from_index(8),
    "brightred":      Color.from_index(9),
    "brightgreen":    Color.from_index(10),
    "brightyellow":   Color.from_index(11),
    "brightblue":     Color.from_index(12),
    "brightmagenta":  Color.from_index(13),
    "brightcyan":     Color.from_index(14),
    "brightwhite":    Color.from_index(15),
}


def _pyte_color_to_runtui(color_val: str, default: Color) -> Color:
    """Convert a pyte color value to a runtui Color."""
    if color_val == "default":
        return default
    # Named ANSI color
    named = _PYTE_NAMED_COLORS.get(color_val)
    if named is not None:
        return named
    # Hex color string (6 hex digits, e.g. "ff8000")
    if len(color_val) == 6:
        try:
            return Color.from_hex(color_val)
        except (ValueError, IndexError):
            pass
    return default


def _pyte_attrs_to_runtui(char: pyte.screens.Char) -> Attrs:
    """Convert pyte character attributes to runtui Attrs flags."""
    attrs = Attrs.NONE
    if char.bold:
        attrs |= Attrs.BOLD
    if char.italics:
        attrs |= Attrs.ITALIC
    if char.underscore:
        attrs |= Attrs.UNDERLINE
    if char.strikethrough:
        attrs |= Attrs.STRIKETHROUGH
    if char.reverse:
        attrs |= Attrs.REVERSE
    return attrs


def _copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard (best-effort)."""
    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE).communicate(text.encode("utf-8"))
        elif system == "Linux":
            # Try xclip first, then xsel
            for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
                try:
                    subprocess.Popen(cmd, stdin=subprocess.PIPE).communicate(text.encode("utf-8"))
                    return
                except FileNotFoundError:
                    continue
    except Exception:
        pass


# ---------------------------------------------------------------------------
#  TerminalWidget
# ---------------------------------------------------------------------------

class TerminalWidget(Widget):
    """PTY-based terminal emulator widget.

    Call ``set_backend(backend)`` before ``start()`` to enable the
    zero-thread PTY data path (backend polls the PTY fd in its select
    loop).  If no backend is set, a fallback polling mode is used.
    """

    HISTORY_SIZE = 2000

    def __init__(
        self,
        shell: str = "",
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 80,
        height: int = 24,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        default_shell = (
            os.environ.get("COMSPEC", "cmd.exe")
            if os.name == "nt"
            else os.environ.get("SHELL", "/bin/bash")
        )
        self._shell = shell or default_shell
        self._running = False
        self.can_focus = True

        # PTY process
        self._pty: PtyProcess = PtyProcess()

        # pyte virtual terminal
        self._screen: pyte.HistoryScreen | None = None
        self._stream: pyte.Stream | None = None

        # Backend reference for fd registration
        self._backend: Backend | None = None

        # Scrollback browsing offset (0 = live view, >0 = scrolled into history)
        self._scroll_offset = 0

        # Scrollbar drag state
        self._sb_dragging = False
        self._sb_drag_offset = 0

        # Track the last known content size for resize detection
        self._last_rows = 0
        self._last_cols = 0

        # Whether child has exited
        self._child_exited = False
        self._exit_code: int | None = None

        # Text selection state: (row, col) in pyte buffer coordinates
        # row is relative to virtual view (0 = first visible row)
        self._sel_anchor: tuple[int, int] | None = None  # start of selection
        self._sel_end: tuple[int, int] | None = None      # end of selection
        self._sel_dragging = False

        # PTY polling fallback (for backends without fd registration)
        self._poll_thread: threading.Thread | None = None
        self._poll_stop = threading.Event()
        self._using_backend_polling = False

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    @property
    def is_running(self) -> bool:
        return self._running

    def set_backend(self, backend: Backend) -> None:
        """Set the backend so the widget can register its PTY fd."""
        self._backend = backend

    def start(self, command: str = "") -> None:
        """Start the terminal.

        Args:
            command: If given, run this command.  If empty, start the
                     user's default shell.
        """
        if self._running:
            return

        sr = self._screen_rect
        rows = sr.height if sr.height > 0 else self.height
        cols = (sr.width - 1) if sr.width > 1 else (self.width - 1)  # -1 for scrollbar
        rows = max(1, rows)
        cols = max(1, cols)

        # Create pyte screen + stream
        self._screen = pyte.HistoryScreen(cols, rows, history=self.HISTORY_SIZE)
        self._screen.set_mode(pyte.modes.LNM)  # auto-newline
        self._stream = pyte.Stream(self._screen)

        # Build argv
        if command:
            argv = self._build_command_argv(command)
        else:
            argv = self._build_default_shell_argv()

        # Build env
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLUMNS"] = str(cols)
        env["LINES"] = str(rows)
        # Remove NO_COLOR if set — we want colors now
        env.pop("NO_COLOR", None)

        self._pty.spawn(argv, rows=rows, cols=cols, env=env)
        self._running = True
        self._child_exited = False
        self._exit_code = None
        self._scroll_offset = 0
        self._last_rows = rows
        self._last_cols = cols

        # Register the PTY master fd with the backend for select()-based polling
        backend_supports_poll = self._backend_supports_pty_polling()
        if backend_supports_poll and self._pty.master_fd >= 0:
            self._backend.register_pty_fd(self._pty.master_fd, self._on_pty_data)
            self._using_backend_polling = True
        else:
            self._start_poll_thread()

        self.invalidate()

    def _build_command_argv(self, command: str) -> list[str]:
        """Build the argv for launching the shell with a specific command."""
        if os.name == "nt":
            shell_lower = self._shell.lower()
            if "powershell" in shell_lower or shell_lower.endswith("pwsh.exe"):
                return [self._shell, "-NoLogo", "-Command", command]
            return [self._shell, "/C", command]
        return [self._shell, "-c", command]

    def _build_default_shell_argv(self) -> list[str]:
        """Build argv for launching an interactive shell session."""
        if os.name == "nt":
            shell_lower = self._shell.lower()
            if "powershell" in shell_lower or shell_lower.endswith("pwsh.exe"):
                return [self._shell, "-NoLogo"]
            return [self._shell]
        return [self._shell, "-l"]

    def _on_pty_data(self, data: bytes) -> None:
        """Callback invoked by the backend when PTY master fd has data."""
        if not data:
            # Empty data means the fd errored — child probably died
            self._check_child_exit()
            return
        if self._stream is None:
            return
        try:
            text = data.decode("utf-8", errors="replace")
            self._stream.feed(text)
        except Exception:
            pass
        # If user is at the live view (not scrolled up), stay there
        if self._scroll_offset == 0:
            pass  # Already at bottom
        self.invalidate()

    def _check_child_exit(self) -> None:
        """Check if the child process has exited and update state."""
        if self._child_exited:
            return
        rc = self._pty.poll()
        if rc is not None:
            self._child_exited = True
            self._exit_code = rc
            self.invalidate()

    # --- Display ---

    def measure(self, available: Size) -> Size:
        return Size(self.width or available.width, self.height or available.height)

    def arrange(self, rect: Rect) -> None:
        """Called when the widget's layout rect changes — resize the PTY."""
        super().arrange(rect)
        if not self._running or self._screen is None:
            return
        rows = max(1, rect.height)
        cols = max(1, rect.width - 1)  # -1 for scrollbar
        if rows != self._last_rows or cols != self._last_cols:
            self._last_rows = rows
            self._last_cols = cols
            self._screen.resize(rows, cols)
            self._pty.resize(rows, cols)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width
        h = sr.height

        default_fg = Color.from_rgb(200, 200, 200)
        default_bg = Color.from_rgb(30, 30, 30)

        # Reserve 1 column for the scrollbar
        content_w = max(1, w - 1)

        # Fill background
        painter.fill_rect(lx, ly, content_w, h, bg=default_bg)

        if self._screen is None:
            # Not started yet
            self._paint_scrollbar(painter, lx + content_w, ly, h)
            return

        screen = self._screen
        history_top = list(screen.history.top) if screen.history.top else []
        total_history = len(history_top)

        # Clamp scroll offset
        self._scroll_offset = max(0, min(self._scroll_offset, total_history))

        if self._scroll_offset > 0:
            # We're scrolled into history
            self._paint_with_history(painter, lx, ly, content_w, h,
                                     screen, history_top, default_fg, default_bg)
        else:
            # Live view — render directly from pyte screen buffer
            self._paint_live(painter, lx, ly, content_w, h,
                             screen, default_fg, default_bg)

        # Draw cursor when live (not scrolled) and focused
        if self._scroll_offset == 0 and self._focused and not self._child_exited:
            cy = screen.cursor.y
            cx = screen.cursor.x
            if 0 <= cy < h and 0 <= cx < content_w:
                char_at = screen.buffer[cy][cx]
                ch = char_at.data if char_at.data.strip() else " "
                painter.put_char(
                    lx + cx, ly + cy, ch,
                    default_bg, default_fg, Attrs.NONE,
                )

        # Exit message overlay
        if self._child_exited:
            msg = f"[Process exited with code {self._exit_code}]"
            msg_row = min(h - 1, (screen.cursor.y + 1) if screen else 0)
            painter.put_str(
                lx, ly + msg_row, msg,
                fg=Color.from_rgb(255, 200, 100), bg=default_bg,
                max_width=content_w,
            )

        # Scrollbar
        self._paint_scrollbar(painter, lx + content_w, ly, h)

    def _paint_live(self, painter: Painter, lx: int, ly: int,
                    content_w: int, h: int, screen: pyte.HistoryScreen,
                    default_fg: Color, default_bg: Color) -> None:
        """Render the live pyte screen buffer."""
        history_len = len(screen.history.top) if screen.history.top else 0
        for row in range(min(h, screen.lines)):
            vrow = history_len + row
            line = screen.buffer[row]
            for col in range(min(content_w, screen.columns)):
                char = line[col]
                # pyte uses empty data for the continuation cell of a wide char;
                # skip it so the wide-char marker set by put_char is preserved.
                if char.data == "":
                    continue
                ch = char.data
                fg = _pyte_color_to_runtui(char.fg, default_fg)
                bg = _pyte_color_to_runtui(char.bg, default_bg)
                attrs = _pyte_attrs_to_runtui(char)
                if self._is_selected(vrow, col):
                    fg, bg = bg, fg
                painter.put_char(lx + col, ly + row, ch, fg, bg, attrs)

    def _paint_with_history(self, painter: Painter, lx: int, ly: int,
                            content_w: int, h: int, screen: pyte.HistoryScreen,
                            history_top: list, default_fg: Color,
                            default_bg: Color) -> None:
        """Render a view that includes scrollback history lines."""
        total_history = len(history_top)
        # Build a virtual view: history lines + screen lines
        # The view starts at (total_history - scroll_offset) from the top of history
        view_start = total_history - self._scroll_offset

        for display_row in range(h):
            source_idx = view_start + display_row
            if source_idx < 0:
                continue
            if source_idx < total_history:
                # Rendering a history line
                hist_line = history_top[source_idx]
                for col in range(content_w):
                    char = hist_line[col]
                    if char.data == "":
                        continue
                    ch = char.data
                    fg = _pyte_color_to_runtui(char.fg, default_fg)
                    bg = _pyte_color_to_runtui(char.bg, default_bg)
                    attrs = _pyte_attrs_to_runtui(char)
                    if self._is_selected(source_idx, col):
                        fg, bg = bg, fg
                    painter.put_char(lx + col, ly + display_row, ch, fg, bg, attrs)
            else:
                # Rendering a screen line
                screen_row = source_idx - total_history
                if screen_row < screen.lines:
                    line = screen.buffer[screen_row]
                    for col in range(min(content_w, screen.columns)):
                        char = line[col]
                        if char.data == "":
                            continue
                        ch = char.data
                        fg = _pyte_color_to_runtui(char.fg, default_fg)
                        bg = _pyte_color_to_runtui(char.bg, default_bg)
                        attrs = _pyte_attrs_to_runtui(char)
                        if self._is_selected(source_idx, col):
                            fg, bg = bg, fg
                        painter.put_char(lx + col, ly + display_row, ch, fg, bg, attrs)

    def _paint_scrollbar(self, painter: Painter, sx: int, sy: int, h: int) -> None:
        """Paint a vertical scrollbar on the right edge."""
        track_fg = Color.from_rgb(80, 80, 80)
        thumb_fg = Color.from_rgb(160, 160, 160)
        bg = Color.from_rgb(40, 40, 40)

        history_len = len(self._screen.history.top) if self._screen and self._screen.history.top else 0
        screen_lines = self._screen.lines if self._screen else 0
        total_lines = history_len + screen_lines
        visible_h = h

        if h < 3:
            for row in range(h):
                painter.put_char(sx, sy + row, "░", track_fg, bg)
            return

        # Up / down arrows
        painter.put_char(sx, sy, "▲", thumb_fg, bg)
        painter.put_char(sx, sy + h - 1, "▼", thumb_fg, bg)

        track_h = h - 2
        for i in range(track_h):
            painter.put_char(sx, sy + 1 + i, "░", track_fg, bg)

        # Thumb
        if total_lines > visible_h:
            thumb_size = max(1, track_h * visible_h // total_lines)
            max_scroll = history_len
            if max_scroll > 0:
                # scroll_offset=0 means bottom (live), max_scroll means top
                thumb_pos = (track_h - thumb_size) * (max_scroll - self._scroll_offset) // max_scroll
            else:
                thumb_pos = track_h - thumb_size
            thumb_pos = max(0, min(thumb_pos, track_h - thumb_size))
            for i in range(thumb_size):
                painter.put_char(sx, sy + 1 + thumb_pos + i, "█", thumb_fg, bg)

    # --- Scrollbar helpers ---

    def _sb_thumb_info(self, h: int) -> tuple[int, int]:
        """Return (thumb_size, thumb_pos) for scrollbar of height h."""
        history_len = len(self._screen.history.top) if self._screen and self._screen.history.top else 0
        screen_lines = self._screen.lines if self._screen else 0
        total = history_len + screen_lines
        track_h = h - 2
        if track_h < 1 or total <= h:
            return (track_h, 0)
        thumb_size = max(1, track_h * h // total)
        max_scroll = history_len
        if max_scroll > 0:
            thumb_pos = (track_h - thumb_size) * (max_scroll - self._scroll_offset) // max_scroll
        else:
            thumb_pos = track_h - thumb_size
        return (thumb_size, max(0, min(thumb_pos, track_h - thumb_size)))

    # --- Selection helpers ---

    def _sel_range(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        """Return normalized ((start_row, start_col), (end_row, end_col)) or None."""
        if self._sel_anchor is None or self._sel_end is None:
            return None
        a, b = self._sel_anchor, self._sel_end
        if a == b:
            return None
        if a > b:
            a, b = b, a
        return (a, b)

    def _is_selected(self, row: int, col: int) -> bool:
        """Check if a cell at (row, col) in virtual view coords is selected."""
        sel = self._sel_range()
        if not sel:
            return False
        (sr, sc), (er, ec) = sel
        if row < sr or row > er:
            return False
        if sr == er:
            return sc <= col < ec
        if row == sr:
            return col >= sc
        if row == er:
            return col < ec
        return True

    def _display_row_to_virtual(self, display_row: int) -> int:
        """Convert a display row (0-based on screen) to virtual view row.

        Virtual row 0 = first history line; virtual rows increase downward.
        For live view (scroll_offset=0), virtual row = history_len + display_row.
        """
        history_len = len(self._screen.history.top) if self._screen and self._screen.history.top else 0
        if self._scroll_offset > 0:
            view_start = history_len - self._scroll_offset
            return view_start + display_row
        return history_len + display_row

    def _get_selected_text(self) -> str:
        """Extract the selected text from pyte buffers."""
        sel = self._sel_range()
        if not sel or self._screen is None:
            return ""
        (sr, sc), (er, ec) = sel
        screen = self._screen
        history_top = list(screen.history.top) if screen.history.top else []
        total_history = len(history_top)

        lines: list[str] = []
        for vrow in range(sr, er + 1):
            # Determine the source line
            if vrow < 0:
                continue
            if vrow < total_history:
                line = history_top[vrow]
                cols = len(line)
            else:
                srow = vrow - total_history
                if srow >= screen.lines:
                    continue
                line = screen.buffer[srow]
                cols = screen.columns

            # Collect characters for this row
            row_start = sc if vrow == sr else 0
            row_end = ec if vrow == er else cols
            chars: list[str] = []
            for c in range(row_start, min(row_end, cols)):
                ch = line[c].data
                if ch == "":
                    continue  # skip wide-char continuation
                chars.append(ch if ch else " ")
            lines.append("".join(chars).rstrip())

        return "\n".join(lines)

    def _clear_selection(self) -> None:
        self._sel_anchor = None
        self._sel_end = None
        self._sel_dragging = False

    def copy_selection(self) -> str:
        """Copy selected text to system clipboard. Returns the copied text."""
        text = self._get_selected_text()
        if not text:
            return ""
        _copy_to_clipboard(text)
        return text

    # --- Input handling ---

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused:
            return

        # Any keyboard input snaps back to live view and clears selection
        if self._scroll_offset > 0:
            self._scroll_offset = 0
        self._sb_dragging = False
        self._clear_selection()

        if not self._running:
            event.mark_handled()
            return

        if self._child_exited:
            event.mark_handled()
            return

        # Convert KeyEvent to raw terminal bytes and write to PTY
        raw = encode_key(event)
        if raw:
            self._pty.write(raw)

        event.mark_handled()
        self.invalidate()

    def _handle_mouse(self, event: MouseEvent) -> None:
        sr = self._screen_rect
        rx = event.x - sr.x
        ry = event.y - sr.y
        h = sr.height
        content_w = max(1, sr.width - 1)
        history_len = len(self._screen.history.top) if self._screen and self._screen.history.top else 0
        max_scroll = history_len

        # --- Scrollbar drag ---
        if self._sb_dragging:
            if event.action == MA.DRAG:
                track_h = h - 2
                if track_h > 0 and max_scroll > 0:
                    total = history_len + (self._screen.lines if self._screen else 0)
                    thumb_size = max(1, track_h * h // total)
                    new_thumb_pos = ry - 1 - self._sb_drag_offset
                    max_pos = track_h - thumb_size
                    if max_pos > 0:
                        # Invert: thumb_pos=0 means scroll_offset=max_scroll (top)
                        self._scroll_offset = max(0, min(max_scroll,
                            max_scroll - max_scroll * new_thumb_pos // max_pos))
                self.invalidate()
                event.mark_handled()
                return
            elif event.action == MA.RELEASE:
                self._sb_dragging = False
                event.mark_handled()
                return

        # --- Text selection drag ---
        if self._sel_dragging:
            if event.action == MA.DRAG:
                col = max(0, min(rx, content_w - 1))
                row = max(0, min(ry, h - 1))
                self._sel_end = (self._display_row_to_virtual(row), col)
                self.invalidate()
                event.mark_handled()
                return
            elif event.action == MA.RELEASE:
                col = max(0, min(rx, content_w - 1))
                row = max(0, min(ry, h - 1))
                self._sel_end = (self._display_row_to_virtual(row), col)
                self._sel_dragging = False
                # Auto-copy on mouse release if there's a selection
                if self._sel_range():
                    self.copy_selection()
                self.invalidate()
                event.mark_handled()
                return

        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            self.focus()
            # Click on scrollbar column?
            if rx == content_w and h >= 3:
                self._clear_selection()
                if ry == 0:
                    # Up arrow — scroll up (increase offset)
                    self._scroll_offset = min(max_scroll, self._scroll_offset + 1)
                elif ry == h - 1:
                    # Down arrow — scroll down (decrease offset)
                    self._scroll_offset = max(0, self._scroll_offset - 1)
                else:
                    # Track area
                    track_h = h - 2
                    if max_scroll > 0 and track_h > 0:
                        thumb_size, thumb_pos = self._sb_thumb_info(h)
                        click_pos = ry - 1
                        if thumb_pos <= click_pos < thumb_pos + thumb_size:
                            self._sb_dragging = True
                            self._sb_drag_offset = click_pos - thumb_pos
                        elif click_pos < thumb_pos:
                            self._scroll_offset = min(max_scroll, self._scroll_offset + h)
                        else:
                            self._scroll_offset = max(0, self._scroll_offset - h)
                self.invalidate()
                event.mark_handled()
                return
            # Click in content area — start text selection
            col = max(0, min(rx, content_w - 1))
            row = max(0, min(ry, h - 1))
            vrow = self._display_row_to_virtual(row)
            self._sel_anchor = (vrow, col)
            self._sel_end = (vrow, col)
            self._sel_dragging = True
            self.invalidate()
            event.mark_handled()
        elif event.action == MA.PRESS and event.button == MouseButton.RIGHT:
            # Right-click: copy current selection (if any)
            if self._sel_range():
                self.copy_selection()
            event.mark_handled()
        elif event.button == MouseButton.SCROLL_UP:
            self._scroll_offset = min(max_scroll, self._scroll_offset + 3)
            self.invalidate()
            event.mark_handled()
        elif event.button == MouseButton.SCROLL_DOWN:
            self._scroll_offset = max(0, self._scroll_offset - 3)
            self.invalidate()
            event.mark_handled()

    # --- Cleanup ---

    def stop(self) -> None:
        """Stop the terminal and kill the child process."""
        if self._using_backend_polling and self._backend is not None and self._pty.master_fd >= 0:
            self._backend.unregister_pty_fd(self._pty.master_fd)
        self._stop_poll_thread()
        self._pty.terminate()
        self._running = False

    def write_input(self, text: str) -> None:
        """Write text to the PTY as if the user typed it."""
        if self._running and not self._child_exited:
            self._pty.write(text.encode("utf-8"))

    def write_output(self, text: str) -> None:
        """Feed text directly into the pyte screen (for programmatic use)."""
        if self._stream:
            self._stream.feed(text)
            self.invalidate()

    def __del__(self) -> None:
        try:
            self.stop()
        except Exception:
            pass

    def _backend_supports_pty_polling(self) -> bool:
        if self._backend is None:
            return False
        backend_cls = type(self._backend)
        return backend_cls.register_pty_fd is not Backend.register_pty_fd

    def _start_poll_thread(self) -> None:
        if self._poll_thread and self._poll_thread.is_alive():
            return
        self._poll_stop.clear()

        def _poll_loop() -> None:
            while not self._poll_stop.is_set() and self._running:
                try:
                    data = self._pty.read()
                    if data:
                        self._on_pty_data(data)
                    else:
                        time.sleep(0.01)
                except EOFError:
                    self._on_pty_data(b"")
                    break
                except Exception:
                    time.sleep(0.05)

        self._poll_thread = threading.Thread(target=_poll_loop, name="TerminalWidgetPTY", daemon=True)
        self._poll_thread.start()

    def _stop_poll_thread(self) -> None:
        self._poll_stop.set()
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=0.2)
        self._poll_thread = None
        self._using_backend_polling = False

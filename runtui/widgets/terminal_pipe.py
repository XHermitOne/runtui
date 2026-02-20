"""Embedded terminal emulator widget — pipe-based subprocess execution.

Two modes:
  - Shell mode (no command): shows a prompt, user types commands, each
    command is executed as a hidden subprocess with pipes, output displayed.
  - Command mode (command given): runs the command once, streams output,
    shows exit code when done.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, Modifiers, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Rect, Size
from ..rendering.painter import Painter
from .base import Widget


class PipeTerminalWidget(Widget):
    """Embedded terminal emulator within a window.

    Executes commands via hidden subprocess pipes and displays output.
    In shell mode, provides an interactive prompt where each command
    is run as a separate subprocess.
    """

    MAX_SCROLLBACK = 1000

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
        self._shell = shell or os.environ.get("SHELL", "/bin/sh")
        self._lines: list[str] = [""]
        self._scroll_y = 0
        self._cursor_row = 0
        self._cursor_col = 0
        self._running = False
        self.can_focus = True

        # Current input line (what user is typing at the prompt)
        self._input_line = ""
        self._input_cursor = 0

        # Command history
        self._history: list[str] = []
        self._history_idx = -1

        # Mode: "shell" (interactive) or "command" (one-shot)
        self._mode = "shell"

        # Whether we're currently waiting for a subprocess to finish
        self._executing = False

        # The currently running subprocess (for Ctrl+C)
        self._process: subprocess.Popen | None = None
        self._process_lock = threading.Lock()

        # Working directory (tracks cd)
        self._cwd = os.getcwd()

        # Prompt
        self._prompt = "$ "

        # When True the user is manually browsing history via scrollbar/wheel.
        # _ensure_cursor_visible() will NOT auto-snap while this is set.
        # It resets on any keyboard input.
        self._user_scrolling = False

        # Scrollbar drag state
        self._sb_dragging = False
        self._sb_drag_offset = 0

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, command: str = "") -> None:
        """Start the terminal.

        Args:
            command: If given, run this command and display output (command mode).
                     If empty, start interactive shell mode.
        """
        if self._running:
            return

        self._lines = [""]
        self._cursor_row = 0
        self._cursor_col = 0
        self._scroll_y = 0
        self._input_line = ""
        self._input_cursor = 0
        self._running = True
        self._user_scrolling = False

        if command:
            # Command mode: run the command, show output
            self._mode = "command"
            self._append_text(f"$ {command}\n")
            self._execute_command(command)
        else:
            # Shell mode: show prompt
            self._mode = "shell"
            self._append_text(self._prompt)
            self._sync_cursor_to_end()

        self.invalidate()

    def _append_text(self, text: str) -> None:
        """Append text to the display buffer, handling \\n and \\r."""
        for ch in text:
            if ch == "\n":
                self._cursor_row += 1
                self._cursor_col = 0
                if self._cursor_row >= len(self._lines):
                    self._lines.append("")
            elif ch == "\r":
                self._cursor_col = 0
            elif ch == "\t":
                spaces = 8 - (self._cursor_col % 8)
                for _ in range(spaces):
                    self._put_char(" ")
            elif ch >= " ":
                self._put_char(ch)

        # Trim scrollback
        while len(self._lines) > self.MAX_SCROLLBACK:
            self._lines.pop(0)
            self._cursor_row = max(0, self._cursor_row - 1)

    def _put_char(self, ch: str) -> None:
        """Place character at cursor and advance."""
        while self._cursor_row >= len(self._lines):
            self._lines.append("")
        line = self._lines[self._cursor_row]
        if self._cursor_col > len(line):
            line = line + " " * (self._cursor_col - len(line))
        if self._cursor_col < len(line):
            self._lines[self._cursor_row] = (
                line[:self._cursor_col] + ch + line[self._cursor_col + 1:]
            )
        else:
            self._lines[self._cursor_row] = line + ch
        self._cursor_col += 1

    def _sync_cursor_to_end(self) -> None:
        """Move cursor to end of last line."""
        self._cursor_row = len(self._lines) - 1
        self._cursor_col = len(self._lines[self._cursor_row])

    def _execute_command(self, command: str) -> None:
        """Run a command as a hidden subprocess with pipes.

        A background thread reads stdout/stderr and appends to display.
        """
        self._executing = True
        cmd = command.strip()

        # Handle built-in cd
        if cmd == "cd" or cmd.startswith("cd "):
            self._handle_cd(cmd)
            return

        # Handle built-in clear
        if cmd == "clear":
            self._lines = [""]
            self._cursor_row = 0
            self._cursor_col = 0
            self._scroll_y = 0
            self._executing = False
            if self._mode == "shell":
                self._append_text(self._prompt)
                self._sync_cursor_to_end()
            self.invalidate()
            return

        # Handle exit
        if cmd in ("exit", "quit"):
            self._append_text("Bye.\n")
            self._running = False
            self._executing = False
            self.invalidate()
            return

        # Spawn subprocess
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                cwd=self._cwd,
                env=self._get_env(),
                bufsize=0,
            )
        except Exception as e:
            self._append_text(f"Error: {e}\n")
            self._executing = False
            if self._mode == "shell":
                self._append_text(self._prompt)
                self._sync_cursor_to_end()
            self.invalidate()
            return

        with self._process_lock:
            self._process = proc

        # Reader thread for this command
        t = threading.Thread(
            target=self._reader_thread, args=(proc,), daemon=True
        )
        t.start()

    def _reader_thread(self, proc: subprocess.Popen) -> None:
        """Background thread: read subprocess output and append to display."""
        try:
            while True:
                data = proc.stdout.read(1024)
                if not data:
                    break
                text = data.decode("utf-8", errors="replace")
                # Strip ANSI escape sequences for clean display
                text = self._strip_ansi(text)
                self._append_text(text)
                self.invalidate()
        except Exception:
            pass
        finally:
            proc.wait()
            rc = proc.returncode

            with self._process_lock:
                if self._process is proc:
                    self._process = None

            if self._mode == "command":
                self._append_text(f"\n[Process exited with code {rc}]\n")
                self._executing = False
            else:
                # Shell mode — show next prompt
                # Ensure we're on a new line
                if self._cursor_col > 0:
                    self._append_text("\n")
                self._executing = False
                self._append_text(self._prompt)
                self._sync_cursor_to_end()

            self.invalidate()

    @staticmethod
    def _strip_ansi(text: str) -> str:
        """Remove ANSI escape sequences from text."""
        result = []
        i = 0
        n = len(text)
        while i < n:
            if text[i] == "\x1b" and i + 1 < n:
                if text[i + 1] == "[":
                    # CSI: skip until letter
                    j = i + 2
                    while j < n and not text[j].isalpha():
                        j += 1
                    i = j + 1 if j < n else n
                elif text[i + 1] == "]":
                    # OSC: skip until BEL or ST
                    j = i + 2
                    while j < n and text[j] != "\x07":
                        if text[j] == "\x1b" and j + 1 < n and text[j + 1] == "\\":
                            j += 1
                            break
                        j += 1
                    i = j + 1
                else:
                    i += 2
            elif text[i] == "\x07":
                i += 1  # skip BEL
            else:
                result.append(text[i])
                i += 1
        return "".join(result)

    def _handle_cd(self, cmd: str) -> None:
        """Handle built-in cd command."""
        parts = cmd.split(None, 1)
        if len(parts) < 2:
            target = os.path.expanduser("~")
        else:
            target = os.path.expanduser(parts[1].strip())
            if not os.path.isabs(target):
                target = os.path.join(self._cwd, target)

        target = os.path.normpath(target)
        if os.path.isdir(target):
            self._cwd = target
        else:
            self._append_text(f"cd: no such directory: {parts[1].strip() if len(parts) > 1 else '~'}\n")

        self._executing = False
        if self._mode == "shell":
            self._append_text(self._prompt)
            self._sync_cursor_to_end()
        self.invalidate()

    def _get_env(self) -> dict:
        """Get environment for subprocess."""
        env = os.environ.copy()
        env["TERM"] = "dumb"
        env["NO_COLOR"] = "1"
        env["COLUMNS"] = str(self.width or 80)
        env["LINES"] = str(self.height or 24)
        return env

    # --- Display ---

    def _ensure_cursor_visible(self) -> None:
        """Auto-scroll to keep cursor visible — skipped when user is browsing."""
        if self._user_scrolling:
            return
        h = self._screen_rect.height if self._screen_rect.height > 0 else self.height
        if self._cursor_row < self._scroll_y:
            self._scroll_y = self._cursor_row
        elif self._cursor_row >= self._scroll_y + h:
            self._scroll_y = self._cursor_row - h + 1

    def _max_scroll(self) -> int:
        h = self._screen_rect.height if self._screen_rect.height > 0 else self.height
        return max(0, len(self._lines) - h)

    def measure(self, available: Size) -> Size:
        return Size(self.width or available.width, self.height or available.height)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width
        h = sr.height

        fg = Color.from_rgb(200, 200, 200)
        bg = Color.from_rgb(30, 30, 30)

        # Reserve 1 column for the scrollbar
        content_w = max(1, w - 1)

        painter.fill_rect(lx, ly, content_w, h, bg=bg)

        self._ensure_cursor_visible()

        # Clamp scroll_y
        max_sy = self._max_scroll()
        if self._scroll_y > max_sy:
            self._scroll_y = max_sy

        for row in range(h):
            line_idx = self._scroll_y + row
            if line_idx >= len(self._lines):
                break
            line = self._lines[line_idx]
            if line:
                painter.put_str(lx, ly + row, line, fg=fg, bg=bg, max_width=content_w)

        # Draw cursor (only when NOT in user-scrolling mode or cursor is visible)
        if self._focused and not self._executing:
            cursor_screen_row = self._cursor_row - self._scroll_y
            if 0 <= cursor_screen_row < h and self._cursor_col < content_w:
                line = (
                    self._lines[self._cursor_row]
                    if self._cursor_row < len(self._lines)
                    else ""
                )
                ch = (
                    line[self._cursor_col]
                    if self._cursor_col < len(line)
                    else " "
                )
                painter.put_char(
                    lx + self._cursor_col, ly + cursor_screen_row,
                    ch, bg, fg, Attrs.REVERSE,
                )

        # Draw vertical scrollbar
        self._paint_scrollbar(painter, lx + content_w, ly, h)

    def _paint_scrollbar(self, painter: Painter, sx: int, sy: int, h: int) -> None:
        """Paint a vertical scrollbar on the right edge."""
        total_lines = len(self._lines)
        visible_h = h

        track_fg = Color.from_rgb(80, 80, 80)
        thumb_fg = Color.from_rgb(160, 160, 160)
        bg = Color.from_rgb(40, 40, 40)

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
            scrollable = total_lines - visible_h
            if scrollable > 0:
                thumb_pos = (track_h - thumb_size) * self._scroll_y // scrollable
            else:
                thumb_pos = 0
            thumb_pos = max(0, min(thumb_pos, track_h - thumb_size))
            for i in range(thumb_size):
                painter.put_char(sx, sy + 1 + thumb_pos + i, "█", thumb_fg, bg)

    # --- Scrollbar helpers ---

    def _sb_thumb_info(self, h: int) -> tuple[int, int]:
        """Return (thumb_size, thumb_pos) for scrollbar of height h."""
        total = len(self._lines)
        track_h = h - 2
        if track_h < 1 or total <= h:
            return (track_h, 0)
        thumb_size = max(1, track_h * h // total)
        scrollable = total - h
        if scrollable > 0:
            thumb_pos = (track_h - thumb_size) * self._scroll_y // scrollable
        else:
            thumb_pos = 0
        return (thumb_size, max(0, min(thumb_pos, track_h - thumb_size)))

    # --- Input handling ---

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused:
            return

        # Any keyboard input exits user-scrolling mode and jumps back to cursor
        self._user_scrolling = False
        self._sb_dragging = False

        # Ctrl+C: kill running process
        if (event.key == Keys.CHAR and event.char == "c"
                and Modifiers.CTRL in event.modifiers):
            if self._executing:
                self._kill_current()
            event.mark_handled()
            return

        # While a command is executing, ignore other input
        if self._executing:
            event.mark_handled()
            return

        # Not running or shell mode finished — handle input
        if not self._running:
            event.mark_handled()
            return

        if event.key == Keys.ENTER:
            self._on_enter()
            event.mark_handled()
        elif event.key == Keys.BACKSPACE:
            self._on_backspace()
            event.mark_handled()
        elif event.key == Keys.DELETE:
            self._on_delete()
            event.mark_handled()
        elif event.key == Keys.LEFT:
            if self._input_cursor > 0:
                self._input_cursor -= 1
                self._cursor_col -= 1
                self.invalidate()
            event.mark_handled()
        elif event.key == Keys.RIGHT:
            if self._input_cursor < len(self._input_line):
                self._input_cursor += 1
                self._cursor_col += 1
                self.invalidate()
            event.mark_handled()
        elif event.key == Keys.HOME:
            self._cursor_col -= self._input_cursor
            self._input_cursor = 0
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.END:
            self._cursor_col += len(self._input_line) - self._input_cursor
            self._input_cursor = len(self._input_line)
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.UP:
            self._history_prev()
            event.mark_handled()
        elif event.key == Keys.DOWN:
            self._history_next()
            event.mark_handled()
        elif event.key == Keys.PAGE_UP:
            # Page up through buffer
            h = self._screen_rect.height if self._screen_rect.height > 0 else self.height
            self._user_scrolling = True
            self._scroll_y = max(0, self._scroll_y - h)
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.PAGE_DOWN:
            h = self._screen_rect.height if self._screen_rect.height > 0 else self.height
            ms = self._max_scroll()
            new_sy = min(ms, self._scroll_y + h)
            self._scroll_y = new_sy
            # If we scrolled back to the cursor, exit browsing mode
            if self._scroll_y >= ms:
                self._user_scrolling = False
            else:
                self._user_scrolling = True
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.CHAR and event.char:
            if Modifiers.CTRL not in event.modifiers:
                self._insert_char(event.char)
                event.mark_handled()
            elif event.char == "l":
                # Ctrl+L: clear
                self._execute_command("clear")
                event.mark_handled()
            elif event.char == "u":
                # Ctrl+U: clear line
                self._clear_input()
                event.mark_handled()
            else:
                event.mark_handled()
        elif event.key == Keys.TAB:
            # Simple tab completion: list files
            self._tab_complete()
            event.mark_handled()
        elif event.key == Keys.SPACE:
            self._insert_char(" ")
            event.mark_handled()
        else:
            event.mark_handled()

    def _insert_char(self, ch: str) -> None:
        """Insert a character into the input line."""
        self._input_line = (
            self._input_line[:self._input_cursor]
            + ch
            + self._input_line[self._input_cursor:]
        )
        self._input_cursor += 1
        self._redraw_input_line()

    def _on_backspace(self) -> None:
        if self._input_cursor > 0:
            self._input_line = (
                self._input_line[:self._input_cursor - 1]
                + self._input_line[self._input_cursor:]
            )
            self._input_cursor -= 1
            self._redraw_input_line()

    def _on_delete(self) -> None:
        if self._input_cursor < len(self._input_line):
            self._input_line = (
                self._input_line[:self._input_cursor]
                + self._input_line[self._input_cursor + 1:]
            )
            self._redraw_input_line()

    def _clear_input(self) -> None:
        """Clear the current input line."""
        self._input_line = ""
        self._input_cursor = 0
        self._redraw_input_line()

    def _redraw_input_line(self) -> None:
        """Redraw the current prompt + input on the current line."""
        # Replace the current line content with prompt + input
        prompt_len = len(self._prompt)
        full_line = self._prompt + self._input_line
        self._lines[self._cursor_row] = full_line
        self._cursor_col = prompt_len + self._input_cursor
        self.invalidate()

    def _on_enter(self) -> None:
        """Execute the current input line."""
        cmd = self._input_line.strip()
        self._input_line = ""
        self._input_cursor = 0
        self._history_idx = -1

        # Move to next line
        self._append_text("\n")

        if cmd:
            self._history.append(cmd)
            self._execute_command(cmd)
        else:
            # Empty command — just show prompt again
            self._append_text(self._prompt)
            self._sync_cursor_to_end()
            self.invalidate()

    def _history_prev(self) -> None:
        if not self._history:
            return
        if self._history_idx == -1:
            self._history_idx = len(self._history) - 1
        elif self._history_idx > 0:
            self._history_idx -= 1
        else:
            return
        self._input_line = self._history[self._history_idx]
        self._input_cursor = len(self._input_line)
        self._redraw_input_line()

    def _history_next(self) -> None:
        if self._history_idx == -1:
            return
        if self._history_idx < len(self._history) - 1:
            self._history_idx += 1
            self._input_line = self._history[self._history_idx]
        else:
            self._history_idx = -1
            self._input_line = ""
        self._input_cursor = len(self._input_line)
        self._redraw_input_line()

    def _tab_complete(self) -> None:
        """Simple tab completion for file/directory names."""
        line = self._input_line[:self._input_cursor]
        parts = line.rsplit(" ", 1)
        prefix = parts[-1] if parts else ""
        if not prefix:
            return

        base_dir = self._cwd
        search_dir = base_dir
        search_prefix = prefix

        # If prefix contains /, split into dir and name
        if "/" in prefix:
            dir_part, name_part = prefix.rsplit("/", 1)
            candidate = os.path.join(base_dir, dir_part)
            if os.path.isdir(candidate):
                search_dir = candidate
                search_prefix = name_part

        try:
            entries = os.listdir(search_dir)
            matches = [e for e in entries if e.startswith(search_prefix)]
        except OSError:
            return

        if len(matches) == 1:
            completion = matches[0][len(search_prefix):]
            if os.path.isdir(os.path.join(search_dir, matches[0])):
                completion += "/"
            self._input_line = (
                self._input_line[:self._input_cursor]
                + completion
                + self._input_line[self._input_cursor:]
            )
            self._input_cursor += len(completion)
            self._redraw_input_line()
        elif len(matches) > 1:
            # Show matches
            self._append_text("\n")
            for m in sorted(matches):
                self._append_text(f"  {m}\n")
            self._append_text(self._prompt + self._input_line)
            self._sync_cursor_to_end()
            self._cursor_col = len(self._prompt) + self._input_cursor
            self.invalidate()

    def _kill_current(self) -> None:
        """Kill the currently running subprocess (Ctrl+C)."""
        with self._process_lock:
            proc = self._process
        if proc:
            try:
                proc.kill()
            except Exception:
                pass

    # --- Mouse ---

    def _handle_mouse(self, event: MouseEvent) -> None:
        sr = self._screen_rect
        rx = event.x - sr.x
        ry = event.y - sr.y
        h = sr.height
        content_w = max(1, sr.width - 1)
        ms = self._max_scroll()

        # --- Scrollbar drag ---
        if self._sb_dragging:
            if event.action == MA.DRAG:
                track_h = h - 2
                total = len(self._lines)
                if track_h > 0 and total > h:
                    thumb_size = max(1, track_h * h // total)
                    new_thumb_pos = ry - 1 - self._sb_drag_offset
                    max_pos = track_h - thumb_size
                    if max_pos > 0:
                        self._scroll_y = max(0, min(ms, ms * new_thumb_pos // max_pos))
                self._user_scrolling = True
                self.invalidate()
                event.mark_handled()
                return
            elif event.action == MA.RELEASE:
                self._sb_dragging = False
                event.mark_handled()
                return

        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            self.focus()
            # Click on scrollbar column?
            if rx == content_w and h >= 3:
                self._user_scrolling = True
                if ry == 0:
                    # Up arrow
                    self._scroll_y = max(0, self._scroll_y - 1)
                elif ry == h - 1:
                    # Down arrow
                    self._scroll_y = min(ms, self._scroll_y + 1)
                else:
                    # Track area — check if on thumb (start drag) or above/below (page)
                    track_h = h - 2
                    total = len(self._lines)
                    if total > h and track_h > 0:
                        thumb_size, thumb_pos = self._sb_thumb_info(h)
                        click_pos = ry - 1  # relative to track start
                        if thumb_pos <= click_pos < thumb_pos + thumb_size:
                            # Start thumb drag
                            self._sb_dragging = True
                            self._sb_drag_offset = click_pos - thumb_pos
                        elif click_pos < thumb_pos:
                            self._scroll_y = max(0, self._scroll_y - h)
                        else:
                            self._scroll_y = min(ms, self._scroll_y + h)
                self.invalidate()
                event.mark_handled()
                return
            # Click in content area — don't change scrolling mode, just focus
            event.mark_handled()
        elif event.button == MouseButton.SCROLL_UP:
            self._user_scrolling = True
            self._scroll_y = max(0, self._scroll_y - 3)
            self.invalidate()
            event.mark_handled()
        elif event.button == MouseButton.SCROLL_DOWN:
            new_sy = min(ms, self._scroll_y + 3)
            self._scroll_y = new_sy
            if new_sy >= ms:
                self._user_scrolling = False
            else:
                self._user_scrolling = True
            self.invalidate()
            event.mark_handled()

    # --- Cleanup ---

    def stop(self) -> None:
        """Stop the terminal and kill any running process."""
        self._running = False
        self._kill_current()

    def write_input(self, text: str) -> None:
        """Write text as if user typed it (for programmatic use)."""
        for ch in text:
            if ch == "\n":
                self._on_enter()
            else:
                self._insert_char(ch)

    def write_output(self, text: str) -> None:
        """Append text to display (for programmatic use)."""
        self._append_text(text)
        self._ensure_cursor_visible()
        self.invalidate()

    def __del__(self) -> None:
        self.stop()

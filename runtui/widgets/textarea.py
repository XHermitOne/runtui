"""TextArea widget -- multi-line text editor."""

from __future__ import annotations

from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, Modifiers, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Size
from ..core.unicode import char_width, string_width
from ..rendering.painter import Painter
from .base import Widget


class TextArea(Widget):
    """Multi-line text editing area with scrolling, scrollbars, selection, and search."""

    # Class-level text clipboard shared across all TextArea instances
    # (separate from Finder's file clipboard)
    _shared_text_clipboard: str = ""

    def __init__(
        self,
        text: str = "",
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 40,
        height: int = 10,
        word_wrap: bool = False,
        readonly: bool = False,
        on_change: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        self._lines: list[str] = text.split("\n") if text else [""]
        self.word_wrap = word_wrap
        self.readonly = readonly
        self._on_change = on_change
        self._cursor_row = 0
        self._cursor_col = 0
        self._scroll_y = 0
        self._scroll_x = 0
        self._desired_col = 0  # Remembered column for vertical movement
        self.can_focus = True

        # Undo stack
        self._undo_stack: list[tuple[list[str], int, int]] = []
        self._redo_stack: list[tuple[list[str], int, int]] = []

        # Selection state: (row, col) of selection anchor; None means no selection
        self._sel_anchor: tuple[int, int] | None = None

        # Text clipboard is class-level (_shared_text_clipboard)

        # Search/replace state
        self._search_active = False
        self._search_text = ""
        self._replace_text = ""
        self._search_cursor = 0  # which input field is active: 0=search, 1=replace
        self._search_matches: list[tuple[int, int]] = []  # [(row, col), ...]
        self._search_match_idx = -1

        # Syntax highlighting (set externally via set_syntax)
        self._syntax: "SyntaxHighlighter | None" = None
        self._syntax_cache: dict[int, list] = {}  # line_idx -> color list

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    @property
    def text(self) -> str:
        return "\n".join(self._lines)

    @text.setter
    def text(self, value: str) -> None:
        self._save_undo()
        self._lines = value.split("\n") if value else [""]
        self._cursor_row = 0
        self._cursor_col = 0
        self._sel_anchor = None
        self._syntax_cache.clear()
        self.invalidate()

    @property
    def line_count(self) -> int:
        return len(self._lines)

    # --- Syntax highlighting ---

    def set_syntax(self, highlighter) -> None:
        """Set a SyntaxHighlighter (or None to disable)."""
        self._syntax = highlighter
        self._syntax_cache.clear()
        self.invalidate()

    def _syntax_color(self, line_idx: int, char_idx: int):
        """Return the syntax Color for a character, or None for default."""
        if self._syntax is None:
            return None
        if line_idx not in self._syntax_cache:
            if line_idx < len(self._lines):
                self._syntax_cache[line_idx] = self._syntax.highlight_line(
                    self._lines[line_idx], line_idx
                )
            else:
                return None
        colors = self._syntax_cache[line_idx]
        if char_idx < len(colors):
            return colors[char_idx]
        return None

    # --- Text dimensions for scrollbar ---

    def _text_width(self) -> int:
        """Width of the text editing area (excluding scrollbar)."""
        return max(1, self._screen_rect.width - 1)

    def _text_height(self) -> int:
        """Height of the text editing area (excluding scrollbar)."""
        return max(1, self._screen_rect.height - 1)

    def _max_line_width(self) -> int:
        """Width of the longest line."""
        if not self._lines:
            return 0
        return max(len(line) for line in self._lines)

    # --- Selection helpers ---

    def _sel_range(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        """Return (start, end) of selection as ((row,col),(row,col)), or None."""
        if self._sel_anchor is None:
            return None
        a = self._sel_anchor
        b = (self._cursor_row, self._cursor_col)
        if a == b:
            return None
        return (min(a, b), max(a, b))

    def _get_selected_text(self) -> str:
        """Return the currently selected text."""
        sel = self._sel_range()
        if not sel:
            return ""
        (sr, sc), (er, ec) = sel
        # Clamp to valid bounds
        last_row = len(self._lines) - 1
        sr = min(sr, last_row)
        er = min(er, last_row)
        sc = min(sc, len(self._lines[sr]))
        ec = min(ec, len(self._lines[er]))
        if sr == er:
            return self._lines[sr][sc:ec]
        parts = [self._lines[sr][sc:]]
        for r in range(sr + 1, er):
            parts.append(self._lines[r])
        parts.append(self._lines[er][:ec])
        return "\n".join(parts)

    def _delete_selection(self) -> bool:
        """Delete the selected text. Returns True if something was deleted."""
        sel = self._sel_range()
        if not sel:
            return False
        self._save_undo()
        (sr, sc), (er, ec) = sel
        # Clamp to valid bounds
        last_row = len(self._lines) - 1
        sr = min(sr, last_row)
        er = min(er, last_row)
        sc = min(sc, len(self._lines[sr]))
        ec = min(ec, len(self._lines[er]))
        if sr == er:
            line = self._lines[sr]
            self._lines[sr] = line[:sc] + line[ec:]
        else:
            before = self._lines[sr][:sc]
            after = self._lines[er][ec:]
            self._lines[sr] = before + after
            del self._lines[sr + 1:er + 1]
        self._cursor_row = sr
        self._cursor_col = sc
        self._desired_col = sc
        self._sel_anchor = None
        self._ensure_cursor_visible()
        self.invalidate()
        self._notify_change()
        return True

    def _clear_selection(self) -> None:
        self._sel_anchor = None

    # --- Search helpers ---

    def _find_all_matches(self) -> None:
        """Find all occurrences of _search_text in the document."""
        self._search_matches.clear()
        self._search_match_idx = -1
        if not self._search_text:
            return
        needle = self._search_text.lower()
        for row_idx, line in enumerate(self._lines):
            start = 0
            lower_line = line.lower()
            while True:
                pos = lower_line.find(needle, start)
                if pos == -1:
                    break
                self._search_matches.append((row_idx, pos))
                start = pos + 1

    def _goto_next_match(self) -> None:
        """Jump cursor to the next search match."""
        if not self._search_matches:
            return
        # Find next match after cursor
        cursor_pos = (self._cursor_row, self._cursor_col)
        for i, (r, c) in enumerate(self._search_matches):
            if (r, c) > cursor_pos:
                self._search_match_idx = i
                self._cursor_row = r
                self._cursor_col = c
                self._desired_col = c
                self._ensure_cursor_visible()
                self.invalidate()
                return
        # Wrap around
        self._search_match_idx = 0
        r, c = self._search_matches[0]
        self._cursor_row = r
        self._cursor_col = c
        self._desired_col = c
        self._ensure_cursor_visible()
        self.invalidate()

    def _goto_prev_match(self) -> None:
        """Jump cursor to the previous search match."""
        if not self._search_matches:
            return
        cursor_pos = (self._cursor_row, self._cursor_col)
        for i in range(len(self._search_matches) - 1, -1, -1):
            r, c = self._search_matches[i]
            if (r, c) < cursor_pos:
                self._search_match_idx = i
                self._cursor_row = r
                self._cursor_col = c
                self._desired_col = c
                self._ensure_cursor_visible()
                self.invalidate()
                return
        # Wrap around
        self._search_match_idx = len(self._search_matches) - 1
        r, c = self._search_matches[-1]
        self._cursor_row = r
        self._cursor_col = c
        self._desired_col = c
        self._ensure_cursor_visible()
        self.invalidate()

    def _replace_current(self) -> None:
        """Replace the current match with _replace_text, then advance to next."""
        if not self._search_matches:
            return
        # If no current match selected, find the next one first
        if self._search_match_idx < 0:
            self._goto_next_match()
            return
        r, c = self._search_matches[self._search_match_idx]
        n = len(self._search_text)
        self._save_undo()
        line = self._lines[r]
        # Do case-preserving replacement at exact position
        self._lines[r] = line[:c] + self._replace_text + line[c + n:]
        self._cursor_row = r
        self._cursor_col = c + len(self._replace_text)
        self._desired_col = self._cursor_col
        self._notify_change()
        # Rebuild matches and auto-advance to next match
        self._find_all_matches()
        self._select_nearest_match()
        self._ensure_cursor_visible()
        self.invalidate()

    def _select_nearest_match(self) -> None:
        """Set _search_match_idx to the match at or after the cursor."""
        if not self._search_matches:
            self._search_match_idx = -1
            return
        cursor_pos = (self._cursor_row, self._cursor_col)
        for i, (r, c) in enumerate(self._search_matches):
            if (r, c) >= cursor_pos:
                self._search_match_idx = i
                return
        # Wrap around to first match
        self._search_match_idx = 0

    def _replace_all(self) -> None:
        """Replace all matches (case-insensitive, matching search behavior)."""
        if not self._search_text:
            return
        self._save_undo()
        needle_lower = self._search_text.lower()
        n = len(self._search_text)
        # Replace from end to start to preserve positions
        for r in range(len(self._lines) - 1, -1, -1):
            line = self._lines[r]
            lower_line = line.lower()
            pos = len(lower_line)
            while True:
                pos = lower_line.rfind(needle_lower, 0, pos)
                if pos == -1:
                    break
                line = line[:pos] + self._replace_text + line[pos + n:]
                lower_line = line.lower()
            self._lines[r] = line
        self._notify_change()
        self._find_all_matches()
        self._search_match_idx = 0 if self._search_matches else -1
        self.invalidate()

    def measure(self, available: Size) -> Size:
        return Size(self.width or available.width, self.height or available.height)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width
        h = sr.height

        if self._focused:
            fg = self.theme_color("input.focused.fg", Color.WHITE)
            bg = self.theme_color("input.focused.bg", Color.BLUE)
        else:
            fg = self.theme_color("input.fg", Color.BLACK)
            bg = self.theme_color("input.bg", Color.CYAN)

        # Reserve space for scrollbars
        text_w = max(1, w - 1)  # 1 col for vertical scrollbar
        text_h = max(1, h - 1)  # 1 row for horizontal scrollbar

        # If search bar is active, reduce text area height by 2
        search_rows = 2 if self._search_active else 0
        content_h = max(1, text_h - search_rows)

        # Fill background
        painter.fill_rect(lx, ly, text_w, content_h, bg=bg)

        # Get selection range
        sel = self._sel_range()
        sel_fg = self.theme_color("input.selection.fg", Color.BLACK)
        sel_bg = self.theme_color("input.selection.bg", Color.WHITE)

        # Highlight colors for search matches
        match_fg = Color.BLACK
        match_bg = Color.YELLOW
        cur_match_bg = Color.from_rgb(255, 140, 0)  # orange for current match

        # Draw visible lines
        for row in range(content_h):
            line_idx = self._scroll_y + row
            if line_idx >= len(self._lines):
                break
            line = self._lines[line_idx]

            # Draw character by character for selection + search + syntax highlighting
            for col in range(text_w):
                char_idx = self._scroll_x + col
                if char_idx >= len(line):
                    break
                ch = line[char_idx]
                syn = self._syntax_color(line_idx, char_idx)
                cfx, cbx = (syn if syn else fg), bg

                # Check if in selection
                if sel:
                    (sr_, sc), (er, ec) = sel
                    in_sel = False
                    if sr_ == er and line_idx == sr_:
                        in_sel = sc <= char_idx < ec
                    elif line_idx == sr_:
                        in_sel = char_idx >= sc
                    elif line_idx == er:
                        in_sel = char_idx < ec
                    elif sr_ < line_idx < er:
                        in_sel = True
                    if in_sel:
                        cfx, cbx = sel_fg, sel_bg

                # Check if in search match
                if self._search_active and self._search_text:
                    slen = len(self._search_text)
                    for mi, (mr, mc) in enumerate(self._search_matches):
                        if mr == line_idx and mc <= char_idx < mc + slen:
                            if mi == self._search_match_idx:
                                cfx, cbx = match_fg, cur_match_bg
                            else:
                                cfx, cbx = match_fg, match_bg
                            break

                painter.put_char(lx + col, ly + row, ch, cfx, cbx)

            # Fill remaining columns with background
            line_visible_len = min(text_w, max(0, len(line) - self._scroll_x))
            if line_visible_len < text_w:
                # Check if trailing part has selection highlight
                for col in range(line_visible_len, text_w):
                    cfx, cbx = fg, bg
                    if sel:
                        (sr_, sc), (er, ec) = sel
                        # Selection extends past line end on intermediate lines
                        if sr_ <= line_idx < er and col + self._scroll_x >= len(line):
                            cfx, cbx = sel_fg, sel_bg
                    painter.put_char(lx + col, ly + row, " ", cfx, cbx)

        # Draw cursor
        if self._focused and not self._search_active:
            cursor_screen_row = self._cursor_row - self._scroll_y
            cursor_screen_col = self._cursor_col - self._scroll_x
            if 0 <= cursor_screen_row < content_h and 0 <= cursor_screen_col < text_w:
                line = self._lines[self._cursor_row] if self._cursor_row < len(self._lines) else ""
                ch = line[self._cursor_col] if self._cursor_col < len(line) else " "
                painter.put_char(
                    lx + cursor_screen_col,
                    ly + cursor_screen_row,
                    ch, fg, bg, Attrs.REVERSE,
                )

        # --- Draw vertical scrollbar ---
        self._paint_vscrollbar(painter, lx + text_w, ly, 1, content_h, bg)

        # --- Draw horizontal scrollbar ---
        self._paint_hscrollbar(painter, lx, ly + content_h, text_w, 1, bg)

        # --- Draw corner (intersection of scrollbars) ---
        corner_bg = self.theme_color("scrollbar.bg", Color.DEFAULT)
        painter.put_char(lx + text_w, ly + content_h, " ", bg=corner_bg)

        # --- Draw search bar if active ---
        if self._search_active:
            self._paint_search_bar(painter, lx, ly + content_h + 1, w)

    def _paint_vscrollbar(self, painter: Painter, lx: int, ly: int, w: int, h: int, text_bg: Color) -> None:
        """Paint vertical scrollbar."""
        track_fg = self.theme_color("scrollbar.track", Color.BRIGHT_BLACK)
        thumb_fg = self.theme_color("scrollbar.thumb", Color.WHITE)
        arrow_fg = self.theme_color("scrollbar.arrow", Color.WHITE)
        sb_bg = self.theme_color("scrollbar.bg", Color.DEFAULT)

        total = len(self._lines)
        visible = self._text_height()
        if self._search_active:
            visible = max(1, visible - 2)

        if h < 3:
            for i in range(h):
                painter.put_char(lx, ly + i, "░", track_fg, sb_bg)
            return

        painter.put_char(lx, ly, "▲", arrow_fg, sb_bg)
        painter.put_char(lx, ly + h - 1, "▼", arrow_fg, sb_bg)

        track_h = h - 2
        for i in range(track_h):
            painter.put_char(lx, ly + 1 + i, "░", track_fg, sb_bg)

        if total > visible and track_h > 0:
            thumb_size = max(1, track_h * visible // total)
            scrollable = total - visible
            if scrollable > 0:
                thumb_pos = (track_h - thumb_size) * self._scroll_y // scrollable
            else:
                thumb_pos = 0
            for i in range(thumb_size):
                painter.put_char(lx, ly + 1 + thumb_pos + i, "█", thumb_fg, sb_bg)

    def _paint_hscrollbar(self, painter: Painter, lx: int, ly: int, w: int, h: int, text_bg: Color) -> None:
        """Paint horizontal scrollbar."""
        track_fg = self.theme_color("scrollbar.track", Color.BRIGHT_BLACK)
        thumb_fg = self.theme_color("scrollbar.thumb", Color.WHITE)
        arrow_fg = self.theme_color("scrollbar.arrow", Color.WHITE)
        sb_bg = self.theme_color("scrollbar.bg", Color.DEFAULT)

        total = self._max_line_width()
        visible = self._text_width()

        if w < 3:
            for i in range(w):
                painter.put_char(lx + i, ly, "░", track_fg, sb_bg)
            return

        painter.put_char(lx, ly, "◄", arrow_fg, sb_bg)
        painter.put_char(lx + w - 1, ly, "►", arrow_fg, sb_bg)

        track_w = w - 2
        for i in range(track_w):
            painter.put_char(lx + 1 + i, ly, "░", track_fg, sb_bg)

        if total > visible and track_w > 0:
            thumb_size = max(1, track_w * visible // total)
            scrollable = total - visible
            if scrollable > 0:
                thumb_pos = (track_w - thumb_size) * self._scroll_x // scrollable
            else:
                thumb_pos = 0
            for i in range(thumb_size):
                painter.put_char(lx + 1 + thumb_pos + i, ly, "█", thumb_fg, sb_bg)

    def _paint_search_bar(self, painter: Painter, lx: int, ly: int, w: int) -> None:
        """Paint the search/replace bar at the bottom."""
        bar_fg = Color.WHITE
        bar_bg = Color.from_rgb(60, 60, 60)
        input_fg = Color.WHITE
        input_bg = Color.from_rgb(40, 40, 40)
        active_bg = Color.from_rgb(30, 50, 80)

        # Search row
        painter.fill_rect(lx, ly, w, 1, bg=bar_bg)
        painter.put_str(lx, ly, " Find:", fg=bar_fg, bg=bar_bg)
        search_x = lx + 6
        search_w = max(1, w - 20)
        s_bg = active_bg if self._search_cursor == 0 else input_bg
        painter.fill_rect(search_x, ly, search_w, 1, bg=s_bg)
        painter.put_str(search_x, ly, self._search_text, fg=input_fg, bg=s_bg, max_width=search_w)
        # Cursor in search field
        if self._search_cursor == 0:
            cpos = min(len(self._search_text), search_w - 1)
            ch = self._search_text[cpos] if cpos < len(self._search_text) else " "
            painter.put_char(search_x + cpos, ly, ch, input_fg, s_bg, Attrs.REVERSE)

        # Match count
        match_str = f" {len(self._search_matches)} matches "
        painter.put_str(search_x + search_w + 1, ly, match_str, fg=bar_fg, bg=bar_bg, max_width=w - search_w - 7)

        # Replace row
        painter.fill_rect(lx, ly + 1, w, 1, bg=bar_bg)
        painter.put_str(lx, ly + 1, " Repl:", fg=bar_fg, bg=bar_bg)
        r_bg = active_bg if self._search_cursor == 1 else input_bg
        painter.fill_rect(search_x, ly + 1, search_w, 1, bg=r_bg)
        painter.put_str(search_x, ly + 1, self._replace_text, fg=input_fg, bg=r_bg, max_width=search_w)
        if self._search_cursor == 1:
            cpos = min(len(self._replace_text), search_w - 1)
            ch = self._replace_text[cpos] if cpos < len(self._replace_text) else " "
            painter.put_char(search_x + cpos, ly + 1, ch, input_fg, r_bg, Attrs.REVERSE)

        # Buttons
        btn_x = search_x + search_w + 1
        btn_fg = Color.WHITE
        btn_bg = Color.from_rgb(80, 80, 80)
        painter.put_str(btn_x, ly + 1, "[Repl]", fg=btn_fg, bg=btn_bg)
        painter.put_str(btn_x + 7, ly + 1, "[All]", fg=btn_fg, bg=btn_bg)

    def _ensure_cursor_visible(self) -> None:
        h = self._text_height()
        w = self._text_width()
        if self._search_active:
            h = max(1, h - 2)
        if self._cursor_row < self._scroll_y:
            self._scroll_y = self._cursor_row
        elif self._cursor_row >= self._scroll_y + h:
            self._scroll_y = self._cursor_row - h + 1
        if self._cursor_col < self._scroll_x:
            self._scroll_x = self._cursor_col
        elif self._cursor_col >= self._scroll_x + w:
            self._scroll_x = self._cursor_col - w + 1

    def _save_undo(self) -> None:
        self._undo_stack.append(([*self._lines], self._cursor_row, self._cursor_col))
        self._redo_stack.clear()
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)

    def _undo(self) -> None:
        if not self._undo_stack:
            return
        self._redo_stack.append(([*self._lines], self._cursor_row, self._cursor_col))
        lines, row, col = self._undo_stack.pop()
        self._lines = lines
        self._cursor_row = row
        self._cursor_col = col
        self._sel_anchor = None
        self.invalidate()

    def _redo(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(([*self._lines], self._cursor_row, self._cursor_col))
        lines, row, col = self._redo_stack.pop()
        self._lines = lines
        self._cursor_row = row
        self._cursor_col = col
        self._sel_anchor = None
        self.invalidate()

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused or not self.enabled:
            return

        # --- Search bar key handling ---
        if self._search_active:
            if event.key == Keys.ESCAPE:
                self._search_active = False
                self._search_matches.clear()
                self._search_match_idx = -1
                self.invalidate()
                event.mark_handled()
                return
            if event.key == Keys.TAB:
                self._search_cursor = 1 - self._search_cursor  # toggle
                self.invalidate()
                event.mark_handled()
                return
            if event.key == Keys.ENTER:
                if self._search_cursor == 0:
                    self._find_all_matches()
                    self._goto_next_match()
                else:
                    self._replace_current()
                self.invalidate()
                event.mark_handled()
                return
            # Typing in search/replace fields
            if event.key == Keys.BACKSPACE:
                if self._search_cursor == 0 and self._search_text:
                    self._search_text = self._search_text[:-1]
                    self._find_all_matches()
                elif self._search_cursor == 1 and self._replace_text:
                    self._replace_text = self._replace_text[:-1]
                self.invalidate()
                event.mark_handled()
                return
            if event.key == Keys.CHAR and event.char and Modifiers.CTRL not in event.modifiers:
                if self._search_cursor == 0:
                    self._search_text += event.char
                    self._find_all_matches()
                else:
                    self._replace_text += event.char
                self.invalidate()
                event.mark_handled()
                return
            # Ctrl+G or F3 for next match
            if (event.key == Keys.F3 or
                (event.key == Keys.CHAR and event.char == "g" and Modifiers.CTRL in event.modifiers)):
                self._goto_next_match()
                event.mark_handled()
                return
            # Shift+F3 for prev match
            if event.key == Keys.F3 and Modifiers.SHIFT in event.modifiers:
                self._goto_prev_match()
                event.mark_handled()
                return
            event.mark_handled()
            return

        # --- Ctrl shortcuts (before navigation for selection) ---
        if Modifiers.CTRL in event.modifiers:
            if event.char == "f":
                # Open search bar
                self._search_active = True
                self._search_cursor = 0
                self._find_all_matches()
                self.invalidate()
                event.mark_handled()
                return
            elif event.char == "h":
                # Open search bar with replace focus
                self._search_active = True
                self._search_cursor = 1
                self._find_all_matches()
                self.invalidate()
                event.mark_handled()
                return
            elif event.char == "a":
                # Select all
                self._sel_anchor = (0, 0)
                self._cursor_row = len(self._lines) - 1
                self._cursor_col = len(self._lines[-1])
                self._desired_col = self._cursor_col
                self.invalidate()
                event.mark_handled()
                return
            elif event.char == "c":
                # Copy
                txt = self._get_selected_text()
                if txt:
                    TextArea._shared_text_clipboard = txt
                event.mark_handled()
                return
            elif event.char == "x":
                # Cut
                if not self.readonly:
                    txt = self._get_selected_text()
                    if txt:
                        TextArea._shared_text_clipboard = txt
                        self._delete_selection()
                event.mark_handled()
                return
            elif event.char == "v":
                # Paste
                if not self.readonly and TextArea._shared_text_clipboard:
                    self._delete_selection()
                    self._save_undo()
                    # Insert clipboard text (may be multi-line)
                    clip_lines = TextArea._shared_text_clipboard.split("\n")
                    if len(clip_lines) == 1:
                        self._insert_text(clip_lines[0])
                    else:
                        line = self._lines[self._cursor_row]
                        before = line[:self._cursor_col]
                        after = line[self._cursor_col:]
                        self._lines[self._cursor_row] = before + clip_lines[0]
                        for i, cl in enumerate(clip_lines[1:], 1):
                            if i == len(clip_lines) - 1:
                                self._lines.insert(self._cursor_row + i, cl + after)
                            else:
                                self._lines.insert(self._cursor_row + i, cl)
                        self._cursor_row += len(clip_lines) - 1
                        self._cursor_col = len(clip_lines[-1])
                        self._desired_col = self._cursor_col
                        self._ensure_cursor_visible()
                        self.invalidate()
                        self._notify_change()
                event.mark_handled()
                return

        # --- Navigation with optional Shift selection ---
        shift_held = Modifiers.SHIFT in event.modifiers

        if event.key in (Keys.UP, Keys.DOWN, Keys.LEFT, Keys.RIGHT,
                         Keys.HOME, Keys.END, Keys.PAGE_UP, Keys.PAGE_DOWN):
            if shift_held:
                if self._sel_anchor is None:
                    self._sel_anchor = (self._cursor_row, self._cursor_col)
            else:
                self._sel_anchor = None

        if event.key == Keys.UP:
            if self._cursor_row > 0:
                self._cursor_row -= 1
                line = self._lines[self._cursor_row]
                self._cursor_col = min(self._desired_col, len(line))
                self._ensure_cursor_visible()
                self.invalidate()
            event.mark_handled()
            return
        elif event.key == Keys.DOWN:
            if self._cursor_row < len(self._lines) - 1:
                self._cursor_row += 1
                line = self._lines[self._cursor_row]
                self._cursor_col = min(self._desired_col, len(line))
                self._ensure_cursor_visible()
                self.invalidate()
            event.mark_handled()
            return
        elif event.key == Keys.LEFT:
            if self._cursor_col > 0:
                self._cursor_col -= 1
            elif self._cursor_row > 0:
                self._cursor_row -= 1
                self._cursor_col = len(self._lines[self._cursor_row])
            self._desired_col = self._cursor_col
            self._ensure_cursor_visible()
            self.invalidate()
            event.mark_handled()
            return
        elif event.key == Keys.RIGHT:
            line = self._lines[self._cursor_row]
            if self._cursor_col < len(line):
                self._cursor_col += 1
            elif self._cursor_row < len(self._lines) - 1:
                self._cursor_row += 1
                self._cursor_col = 0
            self._desired_col = self._cursor_col
            self._ensure_cursor_visible()
            self.invalidate()
            event.mark_handled()
            return
        elif event.key == Keys.HOME:
            self._cursor_col = 0
            self._desired_col = 0
            self._ensure_cursor_visible()
            self.invalidate()
            event.mark_handled()
            return
        elif event.key == Keys.END:
            self._cursor_col = len(self._lines[self._cursor_row])
            self._desired_col = self._cursor_col
            self._ensure_cursor_visible()
            self.invalidate()
            event.mark_handled()
            return
        elif event.key == Keys.PAGE_UP:
            self._cursor_row = max(0, self._cursor_row - self._text_height())
            line = self._lines[self._cursor_row]
            self._cursor_col = min(self._desired_col, len(line))
            self._ensure_cursor_visible()
            self.invalidate()
            event.mark_handled()
            return
        elif event.key == Keys.PAGE_DOWN:
            self._cursor_row = min(len(self._lines) - 1, self._cursor_row + self._text_height())
            line = self._lines[self._cursor_row]
            self._cursor_col = min(self._desired_col, len(line))
            self._ensure_cursor_visible()
            self.invalidate()
            event.mark_handled()
            return

        if self.readonly:
            return

        # Ctrl shortcuts (undo/redo)
        if Modifiers.CTRL in event.modifiers:
            if event.char == "z":
                self._undo()
                event.mark_handled()
                return
            elif event.char == "y":
                self._redo()
                event.mark_handled()
                return

        # Editing — delete selection first if present
        if event.key == Keys.ENTER:
            self._delete_selection()
            self._save_undo()
            line = self._lines[self._cursor_row]
            self._lines[self._cursor_row] = line[:self._cursor_col]
            self._lines.insert(self._cursor_row + 1, line[self._cursor_col:])
            self._cursor_row += 1
            self._cursor_col = 0
            self._desired_col = 0
            self._ensure_cursor_visible()
            self.invalidate()
            self._notify_change()
            event.mark_handled()
        elif event.key == Keys.BACKSPACE:
            if self._delete_selection():
                event.mark_handled()
                return
            if self._cursor_col > 0:
                self._save_undo()
                line = self._lines[self._cursor_row]
                self._lines[self._cursor_row] = line[:self._cursor_col - 1] + line[self._cursor_col:]
                self._cursor_col -= 1
                self._desired_col = self._cursor_col
                self.invalidate()
                self._notify_change()
            elif self._cursor_row > 0:
                self._save_undo()
                prev_line = self._lines[self._cursor_row - 1]
                self._cursor_col = len(prev_line)
                self._lines[self._cursor_row - 1] = prev_line + self._lines[self._cursor_row]
                self._lines.pop(self._cursor_row)
                self._cursor_row -= 1
                self._desired_col = self._cursor_col
                self.invalidate()
                self._notify_change()
            event.mark_handled()
        elif event.key == Keys.DELETE:
            if self._delete_selection():
                event.mark_handled()
                return
            line = self._lines[self._cursor_row]
            if self._cursor_col < len(line):
                self._save_undo()
                self._lines[self._cursor_row] = line[:self._cursor_col] + line[self._cursor_col + 1:]
                self.invalidate()
                self._notify_change()
            elif self._cursor_row < len(self._lines) - 1:
                self._save_undo()
                self._lines[self._cursor_row] = line + self._lines[self._cursor_row + 1]
                self._lines.pop(self._cursor_row + 1)
                self.invalidate()
                self._notify_change()
            event.mark_handled()
        elif event.key == Keys.TAB:
            self._delete_selection()
            self._save_undo()
            self._insert_text("    ")
            event.mark_handled()
        elif event.key == Keys.CHAR and event.char and Modifiers.CTRL not in event.modifiers:
            self._delete_selection()
            self._save_undo()
            self._insert_text(event.char)
            event.mark_handled()

    def _insert_text(self, text: str) -> None:
        self._sel_anchor = None
        line = self._lines[self._cursor_row]
        self._lines[self._cursor_row] = line[:self._cursor_col] + text + line[self._cursor_col:]
        self._cursor_col += len(text)
        self._desired_col = self._cursor_col
        self._ensure_cursor_visible()
        self.invalidate()
        self._notify_change()

    def _notify_change(self) -> None:
        self._syntax_cache.clear()
        if self._on_change:
            self._on_change(self.text)

    def _handle_mouse(self, event: MouseEvent) -> None:
        sr = self._screen_rect
        rx = event.x - sr.x
        ry = event.y - sr.y
        text_w = self._text_width()
        text_h = self._text_height()
        search_rows = 2 if self._search_active else 0
        content_h = max(1, text_h - search_rows)

        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            self.focus()

            # Click on vertical scrollbar
            if rx == sr.width - 1 and ry < content_h:
                self._handle_vscrollbar_click(ry, content_h)
                event.mark_handled()
                return

            # Click on horizontal scrollbar
            if ry == content_h and rx < text_w:
                self._handle_hscrollbar_click(rx, text_w)
                event.mark_handled()
                return

            # Click on search bar area
            if self._search_active and ry >= content_h + 1:
                bar_row = ry - content_h - 1
                if 6 <= rx < 6 + max(1, sr.width - 20):
                    self._search_cursor = 0 if bar_row == 0 else 1
                elif bar_row == 1:
                    # Check button clicks
                    btn_x = 6 + max(1, sr.width - 20) + 1
                    if btn_x <= rx < btn_x + 6:
                        self._replace_current()
                    elif btn_x + 7 <= rx < btn_x + 12:
                        self._replace_all()
                self.invalidate()
                event.mark_handled()
                return

            # Click in text area
            if rx < text_w and ry < content_h:
                if self._search_active:
                    # During search, just position cursor (no selection)
                    self._sel_anchor = None
                elif Modifiers.SHIFT in getattr(event, 'modifiers', Modifiers.NONE):
                    if self._sel_anchor is None:
                        self._sel_anchor = (self._cursor_row, self._cursor_col)
                else:
                    self._sel_anchor = (self._scroll_y + ry,
                                       min(self._scroll_x + rx, len(self._lines[min(self._scroll_y + ry, len(self._lines) - 1)])))
                self._cursor_row = min(self._scroll_y + ry, len(self._lines) - 1)
                line = self._lines[self._cursor_row]
                self._cursor_col = min(self._scroll_x + rx, len(line))
                self._desired_col = self._cursor_col
                self.invalidate()
            event.mark_handled()

        elif event.action == MA.DRAG and event.button == MouseButton.LEFT:
            # Extend selection while dragging (only when search is not active)
            if not self._search_active and rx < text_w and ry < content_h:
                self._cursor_row = min(self._scroll_y + ry, len(self._lines) - 1)
                line = self._lines[self._cursor_row]
                self._cursor_col = min(self._scroll_x + rx, len(line))
                self._desired_col = self._cursor_col
                self.invalidate()
            event.mark_handled()

        elif event.button == MouseButton.SCROLL_UP:
            self._scroll_y = max(0, self._scroll_y - 3)
            self.invalidate()
            event.mark_handled()
        elif event.button == MouseButton.SCROLL_DOWN:
            max_scroll = max(0, len(self._lines) - content_h)
            self._scroll_y = min(max_scroll, self._scroll_y + 3)
            self.invalidate()
            event.mark_handled()

    def _handle_vscrollbar_click(self, ry: int, track_total_h: int) -> None:
        """Handle click on the vertical scrollbar area."""
        total = len(self._lines)
        visible = self._text_height()
        if self._search_active:
            visible = max(1, visible - 2)

        if track_total_h < 3:
            return
        if ry == 0:
            self._scroll_y = max(0, self._scroll_y - 1)
        elif ry == track_total_h - 1:
            max_s = max(0, total - visible)
            self._scroll_y = min(max_s, self._scroll_y + 1)
        else:
            # Page scroll
            if ry < track_total_h // 2:
                self._scroll_y = max(0, self._scroll_y - visible)
            else:
                max_s = max(0, total - visible)
                self._scroll_y = min(max_s, self._scroll_y + visible)
        self.invalidate()

    def _handle_hscrollbar_click(self, rx: int, track_total_w: int) -> None:
        """Handle click on the horizontal scrollbar area."""
        total = self._max_line_width()
        visible = self._text_width()

        if track_total_w < 3:
            return
        if rx == 0:
            self._scroll_x = max(0, self._scroll_x - 1)
        elif rx == track_total_w - 1:
            max_s = max(0, total - visible)
            self._scroll_x = min(max_s, self._scroll_x + 1)
        else:
            if rx < track_total_w // 2:
                self._scroll_x = max(0, self._scroll_x - visible)
            else:
                max_s = max(0, total - visible)
                self._scroll_x = min(max_s, self._scroll_x + visible)
        self.invalidate()

"""Screen manager -- double buffering and diff-based flush."""

from __future__ import annotations

from ..backend.base import Backend
from ..core.types import Attrs, Cell, Color, attrs_sequence
from ..core.unicode import char_width as _char_width
from .buffer import CellBuffer


class Screen:
    """Manages double-buffered rendering with diff-based terminal output."""

    def __init__(self, backend: Backend) -> None:
        self._backend = backend
        cols, rows = backend.get_size()
        self.front = CellBuffer(cols, rows)
        self.back = CellBuffer(cols, rows)
        self._width = cols
        self._height = rows

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def resize(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self.front = CellBuffer(width, height)
        self.back = CellBuffer(width, height)

    def clear(self, fg: Color = Color.DEFAULT, bg: Color = Color.DEFAULT) -> None:
        self.back.clear(fg, bg)

    def flush(self) -> None:
        """Diff back vs front buffer and write only changed cells to terminal."""
        output: list[str] = []
        last_fg: Color | None = None
        last_bg: Color | None = None
        last_attrs: Attrs | None = None
        last_x = -2
        last_y = -2

        for y in range(self._height):
            for x in range(self._width):
                back_cell = self.back.get(x, y)
                front_cell = self.front.get(x, y)

                # Skip continuation cells (wide char placeholders)
                if back_cell.wide:
                    continue

                # Check if cell changed. Also force redraw if the front
                # buffer had a wide continuation here that is now gone,
                # or if the wide status changed (emoji replaced by ascii
                # or vice-versa), which can leave ghost half-cells.
                changed = not back_cell.equals(front_cell)
                if not changed and front_cell.wide:
                    # Front was a continuation cell, back is not — must redraw
                    changed = True
                if not changed:
                    # Check if a wide char that WAS at x-1 in front is no
                    # longer there in back — its continuation at x needs clearing
                    if x > 0:
                        prev_front = self.front.get(x - 1, y)
                        prev_back = self.back.get(x - 1, y)
                        prev_front_wide = (prev_front.char and not prev_front.wide
                                           and _char_width(prev_front.char) == 2)
                        prev_back_wide = (prev_back.char and not prev_back.wide
                                          and _char_width(prev_back.char) == 2)
                        if prev_front_wide != prev_back_wide:
                            changed = True

                if not changed:
                    continue

                # Position cursor if not contiguous.
                # After writing a wide char at position p, the terminal
                # cursor advances to p+2.  Account for that.
                expected_x = last_x + 1
                if last_x >= 0 and last_y == y:
                    prev_back = self.back.get(last_x, y)
                    if prev_back.char and not prev_back.wide and _char_width(prev_back.char) == 2:
                        expected_x = last_x + 2

                if y != last_y or x != expected_x:
                    output.append(f"\x1b[{y + 1};{x + 1}H")

                # Update attributes if changed
                if back_cell.attrs != last_attrs:
                    output.append("\x1b[0m")
                    if back_cell.attrs != Attrs.NONE:
                        output.append(attrs_sequence(back_cell.attrs))
                    last_fg = None
                    last_bg = None
                    last_attrs = back_cell.attrs

                # Update colors if changed
                if back_cell.fg != last_fg:
                    output.append(back_cell.fg.fg_sequence())
                    last_fg = back_cell.fg

                if back_cell.bg != last_bg:
                    output.append(back_cell.bg.bg_sequence())
                    last_bg = back_cell.bg

                # Write character
                output.append(back_cell.char if back_cell.char else " ")

                last_x = x
                last_y = y

        if output:
            self._backend.write("".join(output))
            self._backend.flush()

        # Copy back buffer to front buffer
        self.front.copy_from(self.back)

    def force_full_redraw(self) -> None:
        """Mark all front buffer cells as different to force full redraw."""
        for y in range(self._height):
            for x in range(self._width):
                self.front._cells[y][x].char = "\x00"

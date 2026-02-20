"""Calendar picker widget."""

from __future__ import annotations

import calendar
import datetime

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Rect, Size
from ..rendering.painter import Painter
from .base import Widget

from typing import Callable


class Calendar(Widget):
    """Calendar date picker widget.

    Displays a month calendar with navigation.

        February 2026
    Mo Tu We Th Fr Sa Su
                       1
     2  3  4  5  6  7  8
     9 10 11 12 13 14 15
    16 17 18 19 20 21 22
    23 24 25 26 27 28
    [<]   [Today]   [>]
    """

    HEADER_HEIGHT = 2  # Month title + day names
    FOOTER_HEIGHT = 1  # Navigation buttons
    MIN_WIDTH = 22
    MIN_HEIGHT = 10

    def __init__(
        self,
        selected: datetime.date | None = None,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        on_select: Callable[[datetime.date], None] | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=self.MIN_WIDTH, height=self.MIN_HEIGHT)
        self._today = datetime.date.today()
        self._selected = selected or self._today
        self._view_year = self._selected.year
        self._view_month = self._selected.month
        self._on_select = on_select
        self.can_focus = True
        self.min_width = self.MIN_WIDTH
        self.min_height = self.MIN_HEIGHT

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    @property
    def selected(self) -> datetime.date:
        return self._selected

    @selected.setter
    def selected(self, value: datetime.date) -> None:
        self._selected = value
        self._view_year = value.year
        self._view_month = value.month
        self.invalidate()

    def measure(self, available: Size) -> Size:
        return Size(max(self.MIN_WIDTH, self.width), max(self.MIN_HEIGHT, self.height))

    def _prev_month(self) -> None:
        if self._view_month == 1:
            self._view_month = 12
            self._view_year -= 1
        else:
            self._view_month -= 1
        self.invalidate()

    def _next_month(self) -> None:
        if self._view_month == 12:
            self._view_month = 1
            self._view_year += 1
        else:
            self._view_month += 1
        self.invalidate()

    def _go_today(self) -> None:
        self._today = datetime.date.today()
        self._selected = self._today
        self._view_year = self._today.year
        self._view_month = self._today.month
        self.invalidate()
        if self._on_select:
            self._on_select(self._selected)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("calendar.bg", Color.CYAN)
        fg = self.theme_color("calendar.fg", Color.BLACK)
        header_fg = self.theme_color("calendar.header", Color.WHITE)
        today_fg = self.theme_color("calendar.today", Color.YELLOW)
        selected_bg = self.theme_color("calendar.selected", Color.GREEN)

        # Fill background
        painter.fill_rect(lx, ly, sr.width, sr.height, bg=bg)

        # Month/year title
        month_name = calendar.month_name[self._view_month]
        title = f"{month_name} {self._view_year}"
        title_x = lx + (sr.width - len(title)) // 2
        painter.put_str(title_x, ly, title, fg=header_fg, bg=bg, attrs=Attrs.BOLD)

        # Day name headers
        days = "Mo Tu We Th Fr Sa Su"
        painter.put_str(lx, ly + 1, days, fg=header_fg, bg=bg)

        # Calendar grid
        cal = calendar.monthcalendar(self._view_year, self._view_month)
        for week_idx, week in enumerate(cal):
            row_y = ly + 2 + week_idx
            if row_y >= ly + sr.height - 1:
                break
            for day_idx, day in enumerate(week):
                if day == 0:
                    continue
                day_x = lx + day_idx * 3
                day_str = f"{day:2d}"
                date = datetime.date(self._view_year, self._view_month, day)

                if date == self._selected:
                    painter.put_str(day_x, row_y, day_str, fg=fg, bg=selected_bg, attrs=Attrs.BOLD)
                elif date == self._today:
                    painter.put_str(day_x, row_y, day_str, fg=today_fg, bg=bg, attrs=Attrs.BOLD)
                else:
                    painter.put_str(day_x, row_y, day_str, fg=fg, bg=bg)

        # Navigation footer
        footer_y = ly + sr.height - 1
        painter.put_str(lx, footer_y, "[<]", fg=fg, bg=bg)
        today_label = "[Today]"
        painter.put_str(lx + (sr.width - len(today_label)) // 2, footer_y, today_label, fg=fg, bg=bg)
        painter.put_str(lx + sr.width - 3, footer_y, "[>]", fg=fg, bg=bg)

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused:
            return
        if event.key == Keys.LEFT:
            self._move_day(-1)
            event.mark_handled()
        elif event.key == Keys.RIGHT:
            self._move_day(1)
            event.mark_handled()
        elif event.key == Keys.UP:
            self._move_day(-7)
            event.mark_handled()
        elif event.key == Keys.DOWN:
            self._move_day(7)
            event.mark_handled()
        elif event.key == Keys.PAGE_UP:
            self._prev_month()
            event.mark_handled()
        elif event.key == Keys.PAGE_DOWN:
            self._next_month()
            event.mark_handled()
        elif event.key == Keys.ENTER:
            if self._on_select:
                self._on_select(self._selected)
            event.mark_handled()

    def _move_day(self, delta: int) -> None:
        new_date = self._selected + datetime.timedelta(days=delta)
        self._selected = new_date
        self._view_year = new_date.year
        self._view_month = new_date.month
        self.invalidate()

    def _handle_mouse(self, event: MouseEvent) -> None:
        if event.action != MA.PRESS or event.button != MouseButton.LEFT:
            return
        self.focus()

        sr = self._screen_rect
        rx = event.x - sr.x
        ry = event.y - sr.y

        # Footer buttons
        if ry == sr.height - 1:
            if rx < 3:
                self._prev_month()
            elif rx >= sr.width - 3:
                self._next_month()
            else:
                self._go_today()
            event.mark_handled()
            return

        # Day grid (rows start at y offset 2)
        if ry >= 2 and ry < sr.height - 1:
            week_idx = ry - 2
            day_idx = rx // 3
            if 0 <= day_idx < 7:
                cal = calendar.monthcalendar(self._view_year, self._view_month)
                if week_idx < len(cal):
                    day = cal[week_idx][day_idx]
                    if day > 0:
                        self._selected = datetime.date(self._view_year, self._view_month, day)
                        self.invalidate()
                        if self._on_select:
                            self._on_select(self._selected)
            event.mark_handled()

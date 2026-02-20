"""Scrollbar widgets -- horizontal and vertical."""

from __future__ import annotations

from typing import Callable

from ..core.event import MouseEvent
from ..core.keys import MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Size
from ..rendering.painter import Painter
from .base import Widget


class VScrollbar(Widget):
    """Vertical scrollbar."""

    def __init__(
        self,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        height: int = 10,
        total: int = 100,
        visible_amount: int = 10,
        value: int = 0,
        on_change: Callable[[int], None] | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=1, height=height)
        self._total = total
        self._visible_amount = visible_amount
        self._value = value
        self._on_change = on_change
        self.can_focus = False
        self._dragging = False
        self._drag_offset = 0

        self.on(MouseEvent, self._handle_mouse)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int) -> None:
        v = max(0, min(v, self._total - self._visible_amount))
        if self._value != v:
            self._value = v
            self.invalidate()
            if self._on_change:
                self._on_change(v)

    def set_range(self, total: int, visible_amount: int) -> None:
        self._total = max(1, total)
        self._visible_amount = max(1, visible_amount)
        self.value = self._value  # Re-clamp
        self.invalidate()

    def measure(self, available: Size) -> Size:
        return Size(1, self.height or available.height)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        h = sr.height

        track_ch = self.theme_glyph("scrollbar.track", "░")
        thumb_ch = self.theme_glyph("scrollbar.thumb", "█")
        up_ch = self.theme_glyph("scrollbar.up", "▲")
        down_ch = self.theme_glyph("scrollbar.down", "▼")
        track_fg = self.theme_color("scrollbar.track", Color.BRIGHT_BLACK)
        thumb_fg = self.theme_color("scrollbar.thumb", Color.WHITE)
        arrow_fg = self.theme_color("scrollbar.arrow", Color.WHITE)
        bg = self.theme_color("scrollbar.bg", Color.DEFAULT)

        if h < 3:
            return

        # Up arrow
        painter.put_char(lx, ly, up_ch, arrow_fg, bg)
        # Down arrow
        painter.put_char(lx, ly + h - 1, down_ch, arrow_fg, bg)

        # Track
        track_h = h - 2
        for i in range(track_h):
            painter.put_char(lx, ly + 1 + i, track_ch, track_fg, bg)

        # Thumb
        if self._total > self._visible_amount:
            thumb_size = max(1, track_h * self._visible_amount // self._total)
            scrollable = self._total - self._visible_amount
            if scrollable > 0:
                thumb_pos = (track_h - thumb_size) * self._value // scrollable
            else:
                thumb_pos = 0
            for i in range(thumb_size):
                painter.put_char(lx, ly + 1 + thumb_pos + i, thumb_ch, thumb_fg, bg)

    def _handle_mouse(self, event: MouseEvent) -> None:
        sr = self._screen_rect
        ry = event.y - sr.y

        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            h = sr.height
            if ry == 0:
                # Up arrow
                self.value -= 1
            elif ry == h - 1:
                # Down arrow
                self.value += 1
            else:
                # Click on track - page up/down
                track_h = h - 2
                if self._total > self._visible_amount and track_h > 0:
                    thumb_size = max(1, track_h * self._visible_amount // self._total)
                    scrollable = self._total - self._visible_amount
                    thumb_pos = (track_h - thumb_size) * self._value // scrollable if scrollable > 0 else 0
                    click_pos = ry - 1
                    if click_pos < thumb_pos:
                        self.value -= self._visible_amount
                    elif click_pos >= thumb_pos + thumb_size:
                        self.value += self._visible_amount
                    else:
                        self._dragging = True
                        self._drag_offset = click_pos - thumb_pos
            event.mark_handled()

        elif event.action == MA.DRAG and self._dragging:
            track_h = sr.height - 2
            if track_h > 0 and self._total > self._visible_amount:
                thumb_size = max(1, track_h * self._visible_amount // self._total)
                new_thumb_pos = (event.y - sr.y - 1) - self._drag_offset
                scrollable = self._total - self._visible_amount
                max_pos = track_h - thumb_size
                if max_pos > 0:
                    self.value = scrollable * new_thumb_pos // max_pos
            event.mark_handled()

        elif event.action == MA.RELEASE:
            self._dragging = False

        elif event.button == MouseButton.SCROLL_UP:
            self.value -= 3
            event.mark_handled()
        elif event.button == MouseButton.SCROLL_DOWN:
            self.value += 3
            event.mark_handled()


class HScrollbar(Widget):
    """Horizontal scrollbar."""

    def __init__(
        self,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 20,
        total: int = 100,
        visible_amount: int = 10,
        value: int = 0,
        on_change: Callable[[int], None] | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=1)
        self._total = total
        self._visible_amount = visible_amount
        self._value = value
        self._on_change = on_change
        self.can_focus = False
        self._dragging = False
        self._drag_offset = 0

        self.on(MouseEvent, self._handle_mouse)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int) -> None:
        v = max(0, min(v, self._total - self._visible_amount))
        if self._value != v:
            self._value = v
            self.invalidate()
            if self._on_change:
                self._on_change(v)

    def set_range(self, total: int, visible_amount: int) -> None:
        self._total = max(1, total)
        self._visible_amount = max(1, visible_amount)
        self.value = self._value
        self.invalidate()

    def measure(self, available: Size) -> Size:
        return Size(self.width or available.width, 1)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width

        track_ch = self.theme_glyph("scrollbar.track", "░")
        thumb_ch = self.theme_glyph("scrollbar.thumb", "█")
        left_ch = self.theme_glyph("scrollbar.left", "◄")
        right_ch = self.theme_glyph("scrollbar.right", "►")
        track_fg = self.theme_color("scrollbar.track", Color.BRIGHT_BLACK)
        thumb_fg = self.theme_color("scrollbar.thumb", Color.WHITE)
        arrow_fg = self.theme_color("scrollbar.arrow", Color.WHITE)
        bg = self.theme_color("scrollbar.bg", Color.DEFAULT)

        if w < 3:
            return

        # Arrows
        painter.put_char(lx, ly, left_ch, arrow_fg, bg)
        painter.put_char(lx + w - 1, ly, right_ch, arrow_fg, bg)

        # Track
        track_w = w - 2
        for i in range(track_w):
            painter.put_char(lx + 1 + i, ly, track_ch, track_fg, bg)

        # Thumb
        if self._total > self._visible_amount:
            thumb_size = max(1, track_w * self._visible_amount // self._total)
            scrollable = self._total - self._visible_amount
            thumb_pos = (track_w - thumb_size) * self._value // scrollable if scrollable > 0 else 0
            for i in range(thumb_size):
                painter.put_char(lx + 1 + thumb_pos + i, ly, thumb_ch, thumb_fg, bg)

    def _handle_mouse(self, event: MouseEvent) -> None:
        sr = self._screen_rect
        rx = event.x - sr.x

        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            w = sr.width
            if rx == 0:
                self.value -= 1
            elif rx == w - 1:
                self.value += 1
            else:
                track_w = w - 2
                if self._total > self._visible_amount and track_w > 0:
                    thumb_size = max(1, track_w * self._visible_amount // self._total)
                    scrollable = self._total - self._visible_amount
                    thumb_pos = (track_w - thumb_size) * self._value // scrollable if scrollable > 0 else 0
                    click_pos = rx - 1
                    if click_pos < thumb_pos:
                        self.value -= self._visible_amount
                    elif click_pos >= thumb_pos + thumb_size:
                        self.value += self._visible_amount
                    else:
                        self._dragging = True
                        self._drag_offset = click_pos - thumb_pos
            event.mark_handled()

        elif event.action == MA.DRAG and self._dragging:
            track_w = sr.width - 2
            if track_w > 0 and self._total > self._visible_amount:
                thumb_size = max(1, track_w * self._visible_amount // self._total)
                new_thumb_pos = (event.x - sr.x - 1) - self._drag_offset
                scrollable = self._total - self._visible_amount
                max_pos = track_w - thumb_size
                if max_pos > 0:
                    self.value = scrollable * new_thumb_pos // max_pos
            event.mark_handled()

        elif event.action == MA.RELEASE:
            self._dragging = False

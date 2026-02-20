"""Color picker widget."""

from __future__ import annotations

from typing import Callable

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Rect, Size
from ..rendering.painter import Painter
from ..widgets.base import Widget


class ColorPicker(Widget):
    """RGB color picker with sliders and hex input.

    +-- Color Picker ----------------+
    | R: [===|======] 128  #8040FF   |
    | G: [==|========]  64           |
    | B: [==========|] 255          |
    |                                |
    | Preview: [████████]            |
    | [OK]  [Cancel]                 |
    +--------------------------------+
    """

    def __init__(
        self,
        color: Color | None = None,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 36,
        height: int = 8,
        on_change: Callable[[Color], None] | None = None,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=max(30, width), height=max(8, height))
        c = color or Color.from_rgb(128, 128, 128)
        self._r = c.r
        self._g = c.g
        self._b = c.b
        self._active_channel = 0  # 0=R, 1=G, 2=B
        self._on_change = on_change
        self.can_focus = True

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    @property
    def color(self) -> Color:
        return Color.from_rgb(self._r, self._g, self._b)

    @color.setter
    def color(self, value: Color) -> None:
        self._r = value.r
        self._g = value.g
        self._b = value.b
        self.invalidate()

    def _channel_value(self, idx: int) -> int:
        return [self._r, self._g, self._b][idx]

    def _set_channel(self, idx: int, value: int) -> None:
        value = max(0, min(255, value))
        if idx == 0:
            self._r = value
        elif idx == 1:
            self._g = value
        elif idx == 2:
            self._b = value
        self.invalidate()
        if self._on_change:
            self._on_change(self.color)

    def measure(self, available: Size) -> Size:
        return Size(max(30, self.width), max(8, self.height))

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("dialog.bg", Color.BRIGHT_BLACK)
        fg = self.theme_color("dialog.fg", Color.WHITE)

        painter.fill_rect(lx, ly, sr.width, sr.height, bg=bg)

        slider_w = sr.width - 16
        channels = [("R", self._r, Color.from_rgb(255, 0, 0)),
                    ("G", self._g, Color.from_rgb(0, 255, 0)),
                    ("B", self._b, Color.from_rgb(0, 0, 255))]

        for i, (name, value, ch_color) in enumerate(channels):
            row = ly + 1 + i
            is_active = i == self._active_channel and self._focused
            label_attrs = Attrs.BOLD if is_active else Attrs.NONE

            # Label
            painter.put_str(lx + 1, row, f"{name}:", fg=fg, bg=bg, attrs=label_attrs)

            # Slider bar
            slider_x = lx + 4
            filled = int(slider_w * value / 255)
            for col in range(slider_w):
                if col < filled:
                    painter.put_char(slider_x + col, row, "█", ch_color, bg)
                else:
                    painter.put_char(slider_x + col, row, "░", fg, bg)

            # Value
            painter.put_str(slider_x + slider_w + 1, row, f"{value:3d}", fg=fg, bg=bg)

        # Hex value
        hex_str = f"#{self._r:02X}{self._g:02X}{self._b:02X}"
        painter.put_str(lx + 1, ly + 5, f"Hex: {hex_str}", fg=fg, bg=bg)

        # Preview
        preview_color = Color.from_rgb(self._r, self._g, self._b)
        painter.put_str(lx + 1, ly + 6, "Preview: ", fg=fg, bg=bg)
        for col in range(8):
            painter.put_char(lx + 10 + col, ly + 6, "█", preview_color, bg)

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused:
            return
        if event.key == Keys.UP:
            self._active_channel = max(0, self._active_channel - 1)
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.DOWN:
            self._active_channel = min(2, self._active_channel + 1)
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.LEFT:
            v = self._channel_value(self._active_channel)
            self._set_channel(self._active_channel, v - 1)
            event.mark_handled()
        elif event.key == Keys.RIGHT:
            v = self._channel_value(self._active_channel)
            self._set_channel(self._active_channel, v + 1)
            event.mark_handled()
        elif event.key == Keys.HOME:
            self._set_channel(self._active_channel, 0)
            event.mark_handled()
        elif event.key == Keys.END:
            self._set_channel(self._active_channel, 255)
            event.mark_handled()
        elif event.key == Keys.PAGE_UP:
            v = self._channel_value(self._active_channel)
            self._set_channel(self._active_channel, v + 16)
            event.mark_handled()
        elif event.key == Keys.PAGE_DOWN:
            v = self._channel_value(self._active_channel)
            self._set_channel(self._active_channel, v - 16)
            event.mark_handled()

    def _handle_mouse(self, event: MouseEvent) -> None:
        if event.action not in (MA.PRESS, MA.DRAG) or event.button != MouseButton.LEFT:
            return
        self.focus()

        sr = self._screen_rect
        rx = event.x - sr.x
        ry = event.y - sr.y

        # Check if clicking on a slider
        for i in range(3):
            if ry == 1 + i:
                slider_x = 4
                slider_w = sr.width - 16
                if slider_x <= rx < slider_x + slider_w:
                    self._active_channel = i
                    value = int(255 * (rx - slider_x) / (slider_w - 1))
                    self._set_channel(i, value)
                    event.mark_handled()
                    return

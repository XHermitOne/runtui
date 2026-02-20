"""Modal form dialog -- customizable form with labeled fields."""

from __future__ import annotations

from typing import Any

from ..core.types import Color, Rect, Attrs
from ..core.unicode import string_width
from ..rendering.painter import Painter
from ..widgets.base import Widget
from ..widgets.button import Button
from ..widgets.label import Label
from ..widgets.input import TextInput
from ..widgets.checkbox import Checkbox
from ..widgets.dropdown import DropDownList
from .base import Dialog


class FormField:
    """Definition of a form field."""

    def __init__(
        self,
        name: str,
        label: str,
        field_type: str = "text",  # "text", "password", "checkbox", "dropdown"
        default: Any = None,
        options: list[str] | None = None,
        width: int = 30,
    ) -> None:
        self.name = name
        self.label = label
        self.field_type = field_type
        self.default = default
        self.options = options or []
        self.width = width


class FormDialog(Dialog):
    """Modal form dialog with labeled fields."""

    def __init__(
        self,
        title: str = "Form",
        fields: list[FormField] | None = None,
        width: int = 50,
    ) -> None:
        fields = fields or []
        height = max(10, len(fields) * 2 + 7)
        super().__init__(title=title, width=width, height=height)

        self._fields = fields
        self._widgets: dict[str, Widget] = {}

        # Create field widgets
        for field in fields:
            if field.field_type == "text":
                widget = TextInput(
                    text=str(field.default or ""),
                    width=field.width,
                )
            elif field.field_type == "password":
                from ..widgets.password import PasswordInput
                widget = PasswordInput(
                    text=str(field.default or ""),
                    width=field.width,
                )
            elif field.field_type == "checkbox":
                widget = Checkbox(
                    label="",
                    checked=bool(field.default),
                )
            elif field.field_type == "dropdown":
                widget = DropDownList(
                    items=field.options,
                    selected_index=field.default or 0,
                    width=field.width,
                )
            else:
                widget = TextInput(text=str(field.default or ""), width=field.width)

            self._widgets[field.name] = widget
            self.add_child(widget)

        # OK/Cancel buttons
        self._ok_btn = Button(text="OK", on_click=self._on_ok)
        self._cancel_btn = Button(text="Cancel", on_click=lambda: self.close(None))
        self.add_child(self._ok_btn)
        self.add_child(self._cancel_btn)

    def get_values(self) -> dict[str, Any]:
        """Get all field values as a dictionary."""
        result: dict[str, Any] = {}
        for field in self._fields:
            widget = self._widgets.get(field.name)
            if widget is None:
                continue
            if isinstance(widget, Checkbox):
                result[field.name] = widget.checked
            elif isinstance(widget, DropDownList):
                result[field.name] = widget.selected_item
            elif isinstance(widget, TextInput):
                result[field.name] = widget.text
            else:
                result[field.name] = ""
        return result

    def _on_ok(self) -> None:
        self.close(self.get_values())

    def paint(self, painter: Painter) -> None:
        super().paint(painter)

        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("dialog.bg", Color.BRIGHT_BLACK)
        fg = self.theme_color("dialog.fg", Color.BLACK)

        # Draw fields
        label_w = max((string_width(f.label) for f in self._fields), default=8)
        y = ly + 2

        for field in self._fields:
            painter.put_str(lx + 2, y, field.label + ":", fg=fg, bg=bg, attrs=Attrs.BOLD)

            widget = self._widgets.get(field.name)
            if widget:
                widget._screen_rect = Rect(sr.x + label_w + 4, sr.y + (y - ly), field.width, 1)
                widget.paint(painter)
            y += 2

        # Buttons
        btn_y = ly + sr.height - 3
        self._ok_btn._screen_rect = Rect(sr.x + sr.width - 24, sr.y + sr.height - 3, 10, 1)
        self._cancel_btn._screen_rect = Rect(sr.x + sr.width - 13, sr.y + sr.height - 3, 10, 1)
        self._ok_btn.paint(painter)
        self._cancel_btn.paint(painter)

"""Design surface -- the visual canvas for placing and editing widgets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..core.event import MouseEvent, Phase
from ..core.keys import MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Rect
from ..layout.absolute import AbsoluteLayout
from ..rendering.painter import Painter
from ..widgets.base import Widget
from ..widgets.container import Container
from .schema import WIDGET_REGISTRY


@dataclass
class DesignWidgetInfo:
    """Metadata about a widget placed on the design surface."""
    widget: Widget
    widget_type: str
    widget_id: str
    events: dict[str, str] = field(default_factory=dict)


class DesignSurface(Container):
    """Container that intercepts mouse events for design-mode editing.

    Widgets placed here are selectable and draggable but do NOT respond
    to their normal behavior (clicks, key input, etc.).

    Uses TUNNEL-phase event interception so no existing widget code
    needs to be modified.
    """

    def __init__(self) -> None:
        super().__init__()
        self._layout_manager = AbsoluteLayout()
        self._design_widgets: list[DesignWidgetInfo] = []
        self._selected: DesignWidgetInfo | None = None
        self._dragging = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._id_counters: dict[str, int] = {}

        # External callbacks
        self.on_selection_changed: Callable[[DesignWidgetInfo | None], None] | None = None
        self.on_widget_moved: Callable[[DesignWidgetInfo], None] | None = None

        # Tool state (set by toolbox)
        self.active_tool: str | None = None

        # Register TUNNEL-phase handler to intercept before children
        self.on(MouseEvent, self._handle_design_mouse, phase=Phase.TUNNEL)

    # --- Public API ---

    def add_design_widget(self, widget_type: str, rel_x: int, rel_y: int) -> DesignWidgetInfo | None:
        """Create and place a new widget at the given position (relative to surface)."""
        typedef = WIDGET_REGISTRY.get(widget_type)
        if not typedef:
            return None

        # Auto-generate unique ID
        widget_id = self._generate_id(widget_type)

        # Build constructor kwargs with defaults
        kwargs: dict[str, Any] = {
            "x": rel_x,
            "y": rel_y,
            "width": typedef.default_width,
            "height": typedef.default_height,
        }
        if widget_id:
            kwargs["id"] = widget_id

        # Add type-specific defaults
        for pdef in typedef.properties:
            if pdef.name not in kwargs and pdef.default is not None and pdef.category == "content":
                kwargs[pdef.name] = pdef.default

        # Instantiate the widget
        from .deserializer import _CLASS_MAP, _import_class
        class_info = _CLASS_MAP.get(widget_type)
        if not class_info:
            return None

        cls = _import_class(*class_info)

        # Filter kwargs to only those the constructor accepts
        import inspect
        sig = inspect.signature(cls.__init__)
        valid_params = set(sig.parameters.keys()) - {"self"}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}

        widget = cls(**filtered_kwargs)

        # Disable focus so keys don't reach the widget in design mode
        widget.can_focus = False

        self.add_child(widget)

        info = DesignWidgetInfo(
            widget=widget,
            widget_type=widget_type,
            widget_id=widget_id,
        )
        self._design_widgets.append(info)
        self.select_widget(info)
        return info

    def remove_selected(self) -> None:
        """Remove the currently selected widget."""
        if not self._selected:
            return
        widget = self._selected.widget
        self.remove_child(widget)
        # Remove from AbsoluteLayout cache
        if self._layout_manager and hasattr(self._layout_manager, "_original_positions"):
            self._layout_manager._original_positions.pop(id(widget), None)
        self._design_widgets.remove(self._selected)
        self._selected = None
        self._notify_selection_changed()

    def duplicate_selected(self) -> DesignWidgetInfo | None:
        """Clone the selected widget at a small offset."""
        if not self._selected:
            return None
        info = self._selected
        # Get current position
        orig_pos = self._get_original_pos(info.widget)
        if orig_pos:
            ox, oy, ow, oh = orig_pos
        else:
            ox, oy = info.widget.x, info.widget.y

        new_info = self.add_design_widget(info.widget_type, ox + 2, oy + 1)
        if new_info:
            # Copy content properties
            typedef = WIDGET_REGISTRY.get(info.widget_type)
            if typedef:
                for pdef in typedef.properties:
                    if pdef.category in ("content", "behavior", "appearance"):
                        try:
                            val = getattr(info.widget, pdef.name, None)
                            if val is not None:
                                setattr(new_info.widget, pdef.name, val)
                        except (AttributeError, TypeError):
                            pass
            new_info.events = dict(info.events)
        return new_info

    def select_widget(self, info: DesignWidgetInfo | None) -> None:
        """Set the selected widget."""
        self._selected = info
        self._notify_selection_changed()

    def deselect(self) -> None:
        """Clear selection."""
        self._selected = None
        self._notify_selection_changed()

    @property
    def selected(self) -> DesignWidgetInfo | None:
        return self._selected

    def get_all_widgets(self) -> list[DesignWidgetInfo]:
        return list(self._design_widgets)

    def clear_all(self) -> None:
        """Remove all design widgets."""
        self.clear_children()
        if self._layout_manager and hasattr(self._layout_manager, "_original_positions"):
            self._layout_manager._original_positions.clear()
        self._design_widgets.clear()
        self._selected = None
        self._id_counters.clear()
        self._notify_selection_changed()

    def update_widget_position(self, info: DesignWidgetInfo, new_x: int, new_y: int) -> None:
        """Update a widget's position in the AbsoluteLayout cache."""
        widget = info.widget
        layout = self._layout_manager
        if layout and hasattr(layout, "_original_positions"):
            old = layout._original_positions.get(id(widget))
            w = old[2] if old else widget.width
            h = old[3] if old else widget.height
            layout._original_positions[id(widget)] = (new_x, new_y, w, h)

    def update_widget_size(self, info: DesignWidgetInfo, new_w: int, new_h: int) -> None:
        """Update a widget's size in the AbsoluteLayout cache."""
        widget = info.widget
        layout = self._layout_manager
        if layout and hasattr(layout, "_original_positions"):
            old = layout._original_positions.get(id(widget))
            x = old[0] if old else 0
            y = old[1] if old else 0
            layout._original_positions[id(widget)] = (x, y, new_w, new_h)

    def find_info_by_widget(self, widget: Widget) -> DesignWidgetInfo | None:
        """Find the DesignWidgetInfo for a given widget."""
        for info in self._design_widgets:
            if info.widget is widget:
                return info
        return None

    # --- Painting ---

    def paint(self, painter: Painter) -> None:
        """Paint background with dot grid pattern."""
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("container.bg", Color.DEFAULT)
        fg = self.theme_color("container.fg", Color.DEFAULT)
        grid_fg = Color.from_index(8)  # dark gray dots

        # Fill background
        painter.fill_rect(lx, ly, sr.width, sr.height, bg=bg)

        # Draw dot grid for alignment
        for row in range(sr.height):
            for col in range(sr.width):
                if col % 4 == 0 and row % 2 == 0:
                    painter.put_char(lx + col, ly + row, "·", grid_fg, bg)

    def paint_selection_overlay(self, painter: Painter) -> None:
        """Paint selection highlight over the selected widget.

        Called by the RAD app AFTER all window content is painted.
        """
        if not self._selected:
            return

        widget = self._selected.widget
        sr = widget._screen_rect
        if sr.width == 0 or sr.height == 0:
            return

        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        hi = Color.from_index(11)  # bright yellow

        # Top and bottom edges
        for col in range(-1, sr.width + 1):
            sx = lx + col
            painter.put_char(sx, ly - 1, "─", hi, Color.DEFAULT)
            painter.put_char(sx, ly + sr.height, "─", hi, Color.DEFAULT)

        # Left and right edges
        for row in range(sr.height):
            painter.put_char(lx - 1, ly + row, "│", hi, Color.DEFAULT)
            painter.put_char(lx + sr.width, ly + row, "│", hi, Color.DEFAULT)

        # Corners
        painter.put_char(lx - 1, ly - 1, "┌", hi, Color.DEFAULT)
        painter.put_char(lx + sr.width, ly - 1, "┐", hi, Color.DEFAULT)
        painter.put_char(lx - 1, ly + sr.height, "└", hi, Color.DEFAULT)
        painter.put_char(lx + sr.width, ly + sr.height, "┘", hi, Color.DEFAULT)

        # Corner handles
        handle_fg = Color.from_index(15)  # bright white
        painter.put_char(lx - 1, ly - 1, "◆", handle_fg, Color.DEFAULT)
        painter.put_char(lx + sr.width, ly - 1, "◆", handle_fg, Color.DEFAULT)
        painter.put_char(lx - 1, ly + sr.height, "◆", handle_fg, Color.DEFAULT)
        painter.put_char(lx + sr.width, ly + sr.height, "◆", handle_fg, Color.DEFAULT)

    # --- Mouse handling ---

    def _handle_design_mouse(self, event: MouseEvent) -> None:
        """TUNNEL-phase handler: intercept all mouse events for design mode."""
        sr = self._screen_rect
        # Only handle events within the design surface
        if not sr.contains(event.x, event.y):
            return

        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            # Check if a tool is active (placing a new widget)
            if self.active_tool:
                rel_x = event.x - sr.x
                rel_y = event.y - sr.y
                self.add_design_widget(self.active_tool, rel_x, rel_y)
                self.active_tool = None  # one-shot placement
                event.mark_handled()
                return

            # Check if click is on an existing design widget
            hit_info = self._hit_test_design(event.x, event.y)
            if hit_info:
                self.select_widget(hit_info)
                self._dragging = True
                self._drag_offset_x = event.x - hit_info.widget._screen_rect.x
                self._drag_offset_y = event.y - hit_info.widget._screen_rect.y
            else:
                self.deselect()
            event.mark_handled()

        elif event.action == MA.DRAG:
            if self._dragging and self._selected:
                new_screen_x = event.x - self._drag_offset_x
                new_screen_y = event.y - self._drag_offset_y
                # Convert to relative position within the surface
                rel_x = max(0, new_screen_x - sr.x)
                rel_y = max(0, new_screen_y - sr.y)
                self.update_widget_position(self._selected, rel_x, rel_y)
                self.invalidate_layout()
                if self.on_widget_moved:
                    self.on_widget_moved(self._selected)
            event.mark_handled()

        elif event.action == MA.RELEASE:
            self._dragging = False
            event.mark_handled()

        elif event.action == MA.MOVE:
            # Consume move events over the surface to prevent hover effects
            event.mark_handled()

    def _hit_test_design(self, x: int, y: int) -> DesignWidgetInfo | None:
        """Find which design widget is at screen position (x, y)."""
        # Check in reverse order (topmost first)
        for info in reversed(self._design_widgets):
            if info.widget.visible and info.widget._screen_rect.contains(x, y):
                return info
        return None

    # --- Helpers ---

    def _generate_id(self, widget_type: str) -> str:
        """Generate a unique widget ID like 'btn1', 'lbl2'."""
        prefixes = {
            "Label": "lbl",
            "Button": "btn",
            "TextInput": "inp",
            "PasswordInput": "pwd",
            "Checkbox": "chk",
            "RadioButton": "rad",
            "TextArea": "txt",
            "ListBox": "lst",
            "DropDownList": "ddl",
            "ProgressBar": "prg",
            "Calendar": "cal",
            "VScrollbar": "vsb",
            "HScrollbar": "hsb",
            "ImageWidget": "img",
            "StaticImage": "simg",
        }
        prefix = prefixes.get(widget_type, "wgt")
        count = self._id_counters.get(prefix, 0) + 1
        self._id_counters[prefix] = count
        return f"{prefix}{count}"

    def _get_original_pos(self, widget: Widget) -> tuple[int, int, int, int] | None:
        """Get the original relative position from AbsoluteLayout cache."""
        layout = self._layout_manager
        if layout and hasattr(layout, "_original_positions"):
            return layout._original_positions.get(id(widget))
        return None

    def _notify_selection_changed(self) -> None:
        if self.on_selection_changed:
            self.on_selection_changed(self._selected)

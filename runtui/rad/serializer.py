"""Serialize a design surface's widget tree to JSON."""

from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING

from .schema import WIDGET_REGISTRY

if TYPE_CHECKING:
    from .design_surface import DesignSurface


def _get_prop_value(widget: Any, prop_name: str) -> Any:
    """Read a property value from a live widget."""
    if prop_name == "items":
        val = getattr(widget, "_items", None)
        if val is None:
            val = getattr(widget, "items", [])
        return list(val) if val else []
    if prop_name == "text" and hasattr(widget, "_text"):
        return widget._text
    if prop_name == "label" and hasattr(widget, "label"):
        return widget.label
    if prop_name == "checked" and hasattr(widget, "_checked"):
        return widget._checked
    if prop_name == "selected" and hasattr(widget, "_selected"):
        return widget._selected
    if prop_name == "value" and hasattr(widget, "_value"):
        return widget._value
    if prop_name == "filepath" and hasattr(widget, "_filepath"):
        return widget._filepath
    return getattr(widget, prop_name, None)


def widget_to_dict(widget: Any, type_name: str, widget_id: str,
                   events: dict[str, str],
                   original_pos: tuple[int, int, int, int] | None = None) -> dict:
    """Convert a single design widget to a JSON-serializable dict."""
    typedef = WIDGET_REGISTRY.get(type_name)
    if not typedef:
        return {"type": type_name, "id": widget_id, "props": {}, "events": events}

    props: dict[str, Any] = {}
    for prop_def in typedef.properties:
        if prop_def.name in ("x", "y", "width", "height") and original_pos:
            ox, oy, ow, oh = original_pos
            mapping = {"x": ox, "y": oy, "width": ow, "height": oh}
            val = mapping[prop_def.name]
        else:
            val = _get_prop_value(widget, prop_def.name)

        # Always store layout properties; skip defaults for others
        if prop_def.category == "layout" or val != prop_def.default:
            if val is not None:
                props[prop_def.name] = val

    result: dict[str, Any] = {
        "type": type_name,
        "id": widget_id,
        "props": props,
    }
    if events:
        result["events"] = dict(events)
    return result


def serialize_design(surface: "DesignSurface", app_settings: dict | None = None,
                     menu_data: Any = None) -> dict:
    """Convert a DesignSurface's full widget tree to a JSON-serializable dict."""
    app_settings = app_settings or {}
    widgets = []
    radio_groups: set[str] = set()

    for info in surface.get_all_widgets():
        # Get original position from AbsoluteLayout cache
        orig_pos = None
        layout = surface._layout_manager
        if layout and hasattr(layout, "_original_positions"):
            orig_pos = layout._original_positions.get(id(info.widget))

        w_dict = widget_to_dict(info.widget, info.widget_type, info.widget_id,
                                info.events, orig_pos)
        widgets.append(w_dict)

        # Track radio groups
        if info.widget_type == "RadioButton":
            group = w_dict.get("props", {}).get("group", "")
            if group:
                radio_groups.add(group)

    data: dict[str, Any] = {
        "$schema": "runtui-rad-v1",
        "app": {
            "theme": app_settings.get("theme", "light"),
            "title": app_settings.get("title", "My Application"),
        },
        "windows": [{
            "id": app_settings.get("window_id", "main_window"),
            "title": app_settings.get("window_title", "Main Window"),
            "x": app_settings.get("window_x", 5),
            "y": app_settings.get("window_y", 2),
            "width": app_settings.get("window_width", surface.width or 40),
            "height": app_settings.get("window_height", surface.height or 20),
            "widgets": widgets,
        }],
    }
    if radio_groups:
        data["radio_groups"] = sorted(radio_groups)
    if menu_data and menu_data.menus:
        from .menu_editor import menu_design_to_dict
        data["menus"] = menu_design_to_dict(menu_data)
    return data


def save_json(data: dict, path: str) -> None:
    """Write a design dict to a JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

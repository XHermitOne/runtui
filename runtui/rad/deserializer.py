"""Deserialize JSON designs into live widget trees."""

from __future__ import annotations

import json
from typing import Any

from .schema import WIDGET_REGISTRY


# Maps widget type names to (module_path, class_name)
_CLASS_MAP: dict[str, tuple[str, str]] = {
    "Label":         ("runtui.widgets.label",       "Label"),
    "Button":        ("runtui.widgets.button",      "Button"),
    "TextInput":     ("runtui.widgets.input",        "TextInput"),
    "PasswordInput": ("runtui.widgets.password",      "PasswordInput"),
    "Checkbox":      ("runtui.widgets.checkbox",     "Checkbox"),
    "RadioButton":   ("runtui.widgets.radio",        "RadioButton"),
    "TextArea":      ("runtui.widgets.textarea",     "TextArea"),
    "ListBox":       ("runtui.widgets.listbox",      "ListBox"),
    "DropDownList":  ("runtui.widgets.dropdown",     "DropDownList"),
    "ProgressBar":   ("runtui.widgets.progressbar",  "ProgressBar"),
    "Calendar":      ("runtui.widgets.calendar",     "Calendar"),
    "VScrollbar":    ("runtui.widgets.scrollbar",    "VScrollbar"),
    "HScrollbar":    ("runtui.widgets.scrollbar",    "HScrollbar"),
    "ImageWidget":   ("runtui.widgets.image",        "ImageWidget"),
    "StaticImage":   ("runtui.widgets.static_image", "StaticImage"),
}


def _import_class(module_path: str, class_name: str) -> type:
    """Dynamically import a widget class."""
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def _coerce_value(value: Any, type_str: str) -> Any:
    """Coerce a JSON value to the expected Python type."""
    if type_str == "int":
        return int(value) if value is not None else 0
    elif type_str == "float":
        return float(value) if value is not None else 0.0
    elif type_str == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)
    elif type_str == "str":
        return str(value) if value is not None else ""
    elif type_str == "list[str]":
        if isinstance(value, list):
            return [str(v) for v in value]
        return []
    return value


def deserialize_widget(widget_data: dict,
                       radio_groups: dict[str, Any] | None = None
                       ) -> Any:
    """Create a live runtui widget from a JSON widget descriptor.

    Returns the widget instance.
    """
    widget_type = widget_data["type"]
    props = dict(widget_data.get("props", {}))
    widget_id = widget_data.get("id", "")

    # Look up class
    class_info = _CLASS_MAP.get(widget_type)
    if not class_info:
        raise ValueError(f"Unknown widget type: {widget_type}")

    cls = _import_class(*class_info)
    typedef = WIDGET_REGISTRY.get(widget_type)

    # Build constructor kwargs
    kwargs: dict[str, Any] = {}
    if widget_id:
        kwargs["id"] = widget_id

    # Special handling for RadioButton groups
    group_name = props.pop("group", "")

    if typedef:
        for prop_def in typedef.properties:
            if prop_def.name in props and prop_def.name != "group":
                kwargs[prop_def.name] = _coerce_value(props[prop_def.name], prop_def.prop_type)

    # Handle RadioButton group binding
    if widget_type == "RadioButton" and group_name and radio_groups is not None:
        from runtui.widgets.radio import RadioGroup
        if group_name not in radio_groups:
            radio_groups[group_name] = RadioGroup()
        kwargs["group"] = radio_groups[group_name]

    # Filter kwargs to only those the constructor actually accepts
    import inspect
    sig = inspect.signature(cls.__init__)
    valid_params = set(sig.parameters.keys()) - {"self"}
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}

    widget = cls(**filtered_kwargs)

    # Post-construction setup for special widgets
    if widget_type == "ImageWidget":
        filepath = props.get("filepath", "")
        if filepath and hasattr(widget, "load"):
            widget.load(filepath)

    return widget


def load_menu_data(data: dict):
    """Extract and reconstruct MenuDesignData from a design dict.

    Returns MenuDesignData or None if no menus are present.
    """
    raw = data.get("menus")
    if not raw:
        return None
    from .menu_editor import dict_to_menu_design
    return dict_to_menu_design(raw)


def load_json(path: str) -> dict:
    """Load a JSON design file."""
    with open(path, "r") as f:
        return json.load(f)


def load_design(data: dict) -> list[dict]:
    """Parse a design dict and return window descriptors.

    Each window descriptor has:
      - "window": dict with title, x, y, width, height
      - "widgets": list of (widget, widget_data) tuples
    """
    radio_groups: dict[str, Any] = {}

    # Pre-create radio groups
    for group_name in data.get("radio_groups", []):
        from runtui.widgets.radio import RadioGroup
        radio_groups[group_name] = RadioGroup()

    results = []
    for window_data in data.get("windows", []):
        widget_list = []
        for w_data in window_data.get("widgets", []):
            widget = deserialize_widget(w_data, radio_groups)
            widget_list.append((widget, w_data))

        results.append({
            "window": {
                "id": window_data.get("id", "main_window"),
                "title": window_data.get("title", "Window"),
                "x": window_data.get("x", 5),
                "y": window_data.get("y", 2),
                "width": window_data.get("width", 40),
                "height": window_data.get("height", 20),
            },
            "widgets": widget_list,
        })
    return results

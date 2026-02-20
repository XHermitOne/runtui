"""Widget metadata registry for the RAD designer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PropertyDef:
    """Definition of a single editable widget property."""
    name: str
    prop_type: str      # "str", "int", "float", "bool", "list[str]"
    default: Any = None
    category: str = "layout"  # "layout", "content", "behavior", "appearance"


@dataclass
class WidgetTypeDef:
    """Definition of a widget type for the designer toolbox."""
    name: str
    class_name: str
    icon: str
    properties: list[PropertyDef] = field(default_factory=list)
    default_width: int = 20
    default_height: int = 1
    events: list[str] = field(default_factory=list)


# Common layout properties shared by all widgets
COMMON_PROPERTIES = [
    PropertyDef("x", "int", 0, "layout"),
    PropertyDef("y", "int", 0, "layout"),
    PropertyDef("width", "int", 0, "layout"),
    PropertyDef("height", "int", 1, "layout"),
]


def _make(
    name: str,
    icon: str,
    props: list[PropertyDef] | None = None,
    events: list[str] | None = None,
    default_width: int = 20,
    default_height: int = 1,
) -> WidgetTypeDef:
    all_props = list(COMMON_PROPERTIES)
    if props:
        all_props.extend(props)
    return WidgetTypeDef(
        name=name,
        class_name=name,
        icon=icon,
        properties=all_props,
        default_width=default_width,
        default_height=default_height,
        events=events or [],
    )


WIDGET_REGISTRY: dict[str, WidgetTypeDef] = {}

# -- Display widgets --

WIDGET_REGISTRY["Label"] = _make("Label", "Aa", [
    PropertyDef("text", "str", "", "content"),
    PropertyDef("align", "str", "left", "appearance"),
    PropertyDef("bold", "bool", False, "appearance"),
], default_width=12, default_height=1)

WIDGET_REGISTRY["ProgressBar"] = _make("ProgressBar", "██", [
    PropertyDef("value", "float", 0.0, "content"),
    PropertyDef("max_value", "float", 100.0, "content"),
    PropertyDef("show_percentage", "bool", True, "appearance"),
], default_width=20, default_height=1)

# -- Input widgets --

WIDGET_REGISTRY["Button"] = _make("Button", "[B]", [
    PropertyDef("text", "str", "Button", "content"),
], events=["on_click"], default_width=12, default_height=1)

WIDGET_REGISTRY["TextInput"] = _make("TextInput", "[_]", [
    PropertyDef("text", "str", "", "content"),
    PropertyDef("placeholder", "str", "", "content"),
    PropertyDef("max_length", "int", 0, "behavior"),
], events=["on_change", "on_submit"], default_width=22, default_height=1)

WIDGET_REGISTRY["PasswordInput"] = _make("PasswordInput", "[*]", [
    PropertyDef("text", "str", "", "content"),
    PropertyDef("placeholder", "str", "Password", "content"),
    PropertyDef("mask_char", "str", "●", "appearance"),
    PropertyDef("max_length", "int", 0, "behavior"),
], events=["on_change", "on_submit"], default_width=22, default_height=1)

WIDGET_REGISTRY["Checkbox"] = _make("Checkbox", "[✓]", [
    PropertyDef("label", "str", "Checkbox", "content"),
    PropertyDef("checked", "bool", False, "content"),
], events=["on_change"], default_width=16, default_height=1)

WIDGET_REGISTRY["RadioButton"] = _make("RadioButton", "(*)", [
    PropertyDef("label", "str", "Option", "content"),
    PropertyDef("value", "str", "", "content"),
    PropertyDef("selected", "bool", False, "content"),
    PropertyDef("group", "str", "", "behavior"),
], default_width=16, default_height=1)

WIDGET_REGISTRY["TextArea"] = _make("TextArea", "≡T", [
    PropertyDef("text", "str", "", "content"),
    PropertyDef("word_wrap", "bool", False, "behavior"),
    PropertyDef("readonly", "bool", False, "behavior"),
], events=["on_change"], default_width=30, default_height=8)

# -- List/selection widgets --

WIDGET_REGISTRY["ListBox"] = _make("ListBox", "▤L", [
    PropertyDef("items", "list[str]", [], "content"),
], events=["on_select", "on_activate"], default_width=22, default_height=8)

WIDGET_REGISTRY["DropDownList"] = _make("DropDownList", "▼D", [
    PropertyDef("items", "list[str]", [], "content"),
    PropertyDef("selected_index", "int", 0, "content"),
], events=["on_change"], default_width=22, default_height=1)

WIDGET_REGISTRY["Calendar"] = _make("Calendar", "📅", [
], events=["on_select"], default_width=24, default_height=10)

# -- Scrollbar widgets --

WIDGET_REGISTRY["VScrollbar"] = _make("VScrollbar", "▐S", [
    PropertyDef("total", "int", 100, "behavior"),
    PropertyDef("visible_amount", "int", 10, "behavior"),
    PropertyDef("value", "int", 0, "content"),
], events=["on_change"], default_width=1, default_height=10)

WIDGET_REGISTRY["HScrollbar"] = _make("HScrollbar", "▬S", [
    PropertyDef("total", "int", 100, "behavior"),
    PropertyDef("visible_amount", "int", 10, "behavior"),
    PropertyDef("value", "int", 0, "content"),
], events=["on_change"], default_width=20, default_height=1)

# -- Media widgets --

WIDGET_REGISTRY["StaticImage"] = _make("StaticImage", "🖼", [
    PropertyDef("filepath", "str", "", "content"),
], default_width=40, default_height=12)


def get_widget_types() -> list[str]:
    """Return list of all registered widget type names."""
    return list(WIDGET_REGISTRY.keys())


def get_typedef(type_name: str) -> WidgetTypeDef | None:
    """Look up a widget type definition."""
    return WIDGET_REGISTRY.get(type_name)


def get_constructor_params(type_name: str) -> list[str]:
    """Return the property names that map to constructor kwargs."""
    typedef = WIDGET_REGISTRY.get(type_name)
    if not typedef:
        return []
    # 'group' is special (RadioButton) - not a direct constructor param
    skip = {"group"}
    return [p.name for p in typedef.properties if p.name not in skip]

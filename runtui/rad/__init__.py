"""runtui RAD (Rapid Application Development) module.

Provides widget registry, JSON serialization/deserialization,
Python code generation, and a visual form designer.
"""

from .schema import (
    PropertyDef,
    WidgetTypeDef,
    WIDGET_REGISTRY,
    get_widget_types,
    get_typedef,
)
from .serializer import serialize_design, save_json
from .deserializer import deserialize_widget, load_json, load_design, load_menu_data
from .codegen import generate_python, save_python
from .runner import run_json, preview_in_app
from .design_surface import DesignSurface, DesignWidgetInfo
from .menu_editor import (
    MenuItemData,
    MenuData,
    MenuDesignData,
    MenuEditorDialog,
)

__all__ = [
    "PropertyDef",
    "WidgetTypeDef",
    "WIDGET_REGISTRY",
    "get_widget_types",
    "get_typedef",
    "serialize_design",
    "save_json",
    "deserialize_widget",
    "load_json",
    "load_design",
    "generate_python",
    "save_python",
    "run_json",
    "preview_in_app",
    "DesignSurface",
    "DesignWidgetInfo",
    "load_menu_data",
    "MenuItemData",
    "MenuData",
    "MenuDesignData",
    "MenuEditorDialog",
]

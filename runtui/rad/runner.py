"""Run RAD design files (JSON) as live applications."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .deserializer import load_json, load_design, deserialize_widget

if TYPE_CHECKING:
    from runtui.app import App


def run_json(path: str) -> None:
    """Load a JSON design file and run it as a standalone application."""
    from runtui.app import App
    from runtui.windows.window import Window
    from runtui.widgets.container import Container
    from runtui.layout.absolute import AbsoluteLayout

    data = load_json(path)
    app_cfg = data.get("app", {})
    theme = app_cfg.get("theme", "light")

    class GeneratedApp(App):
        def __init__(self) -> None:
            super().__init__(theme=theme)

        def on_ready(self) -> None:
            window_descs = load_design(data)
            for desc in window_descs:
                win_info = desc["window"]
                win = Window(
                    title=win_info["title"],
                    x=win_info["x"],
                    y=win_info["y"],
                    width=win_info["width"],
                    height=win_info["height"],
                )
                content = Container()
                content._layout_manager = AbsoluteLayout()
                for widget, _w_data in desc["widgets"]:
                    content.add_child(widget)
                win.set_content(content)
                self.add_window(win)

            # Set up menus if present
            if data.get("menus"):
                from .deserializer import load_menu_data
                from .menu_editor import menu_design_to_live
                menu_data = load_menu_data(data)
                if menu_data:
                    menu_bar = menu_design_to_live(menu_data)
                    if menu_bar:
                        self.set_menu(menu_bar)

    app = GeneratedApp()
    app.run()


def preview_in_app(data: dict, app: "App") -> list:
    """Create a preview window inside an existing app from a design dict.

    The preview window contains real (non-design-mode) widgets so
    buttons are clickable, inputs are editable, etc.

    Returns a list of created preview Window objects.
    """
    from runtui.windows.window import Window
    from runtui.widgets.container import Container
    from runtui.layout.absolute import AbsoluteLayout

    preview_windows = []
    window_descs = load_design(data)
    for desc in window_descs:
        win_info = desc["window"]
        win = Window(
            title=f"▶ Preview: {win_info['title']}",
            x=win_info["x"] + 2,
            y=win_info["y"] + 1,
            width=win_info["width"],
            height=win_info["height"],
        )
        content = Container()
        content._layout_manager = AbsoluteLayout()
        for widget, _w_data in desc["widgets"]:
            content.add_child(widget)
        win.set_content(content)
        app.add_window(win)
        preview_windows.append(win)

    # Set up menus if present in preview
    if data.get("menus"):
        from .deserializer import load_menu_data
        from .menu_editor import menu_design_to_live
        menu_data = load_menu_data(data)
        if menu_data:
            menu_bar = menu_design_to_live(menu_data)
            if menu_bar:
                app.set_menu(menu_bar)

    app._needs_repaint = True
    return preview_windows

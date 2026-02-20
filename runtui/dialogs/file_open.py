"""OpenFileDialog -- file browser dialog for opening files."""

from __future__ import annotations

import os
from pathlib import Path

from ..core.event import KeyEvent
from ..core.keys import Keys
from ..core.types import Color, Rect, Attrs
from ..core.unicode import truncate_to_width
from ..rendering.painter import Painter
from ..widgets.button import Button
from ..widgets.input import TextInput
from ..widgets.listbox import ListBox
from .base import Dialog


class OpenFileDialog(Dialog):
    """File browser dialog for selecting a file to open."""

    def __init__(
        self,
        title: str = "Open File",
        initial_dir: str = "",
        filters: list[tuple[str, str]] | None = None,
        width: int = 60,
        height: int = 20,
    ) -> None:
        super().__init__(title=title, width=width, height=height)
        self._current_dir = Path(initial_dir or os.getcwd()).resolve()
        self._filters = filters or [("All Files", "*")]
        self._selected_filter = 0
        self._selected_file: str = ""

        # Widgets
        self._path_input = TextInput(text=str(self._current_dir), width=width - 6)
        self._path_input._on_submit = self._on_path_submit
        self.add_child(self._path_input)

        self._file_list = ListBox(width=width - 6, height=height - 9,
                                  on_activate=self._on_file_activate,
                                  on_select=self._on_file_select)
        self.add_child(self._file_list)

        self._filename_input = TextInput(placeholder="File name", width=width - 6)
        self.add_child(self._filename_input)

        self._ok_btn = Button(text="Open", on_click=self._on_ok)
        self.add_child(self._ok_btn)

        self._cancel_btn = Button(text="Cancel", on_click=lambda: self.close(None))
        self.add_child(self._cancel_btn)

        self._refresh_file_list()

    def _refresh_file_list(self) -> None:
        """Refresh the file list from the current directory."""
        items: list[str] = []
        try:
            # Parent directory
            if self._current_dir.parent != self._current_dir:
                items.append("📁 ..")

            entries = sorted(self._current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            for entry in entries:
                if entry.is_dir():
                    items.append(f"📁 {entry.name}")
                else:
                    # Apply filter
                    if self._matches_filter(entry.name):
                        size = self._format_size(entry.stat().st_size) if entry.exists() else ""
                        items.append(f"📄 {entry.name}  {size}")
        except PermissionError:
            items.append("(Permission denied)")
        except OSError as e:
            items.append(f"(Error: {e})")

        self._file_list.items = items
        self._path_input.text = str(self._current_dir)

    def _matches_filter(self, filename: str) -> bool:
        if self._selected_filter >= len(self._filters):
            return True
        _, pattern = self._filters[self._selected_filter]
        if pattern == "*":
            return True
        exts = pattern.replace("*", "").split(";")
        return any(filename.lower().endswith(ext.strip()) for ext in exts)

    def _format_size(self, size: int) -> str:
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size // 1024}KB"
        else:
            return f"{size // (1024 * 1024)}MB"

    def _on_file_select(self, index: int, item: str) -> None:
        # Extract filename from display string
        name = item.split("  ")[0]
        if name.startswith("📄 "):
            self._filename_input.text = name[2:].strip()

    def _on_file_activate(self, index: int, item: str) -> None:
        name = item.split("  ")[0]
        if name.startswith("📁 "):
            dirname = name[2:].strip()
            if dirname == "..":
                self._current_dir = self._current_dir.parent
            else:
                self._current_dir = self._current_dir / dirname
            self._refresh_file_list()
        elif name.startswith("📄 "):
            self._on_ok()

    def _on_path_submit(self, text: str) -> None:
        path = Path(text)
        if path.is_dir():
            self._current_dir = path.resolve()
            self._refresh_file_list()

    def _on_ok(self) -> None:
        filename = self._filename_input.text
        if filename:
            full_path = self._current_dir / filename
            self.close(str(full_path))
        else:
            self.close(None)

    def paint(self, painter: Painter) -> None:
        super().paint(painter)

        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("dialog.bg", Color.BRIGHT_BLACK)
        fg = self.theme_color("dialog.fg", Color.BLACK)

        # Label: Path
        painter.put_str(lx + 2, ly + 2, "Path:", fg=fg, bg=bg, attrs=Attrs.BOLD)

        # Path input
        self._path_input._screen_rect = Rect(sr.x + 2, sr.y + 3, sr.width - 6, 1)
        self._path_input.paint(painter)

        # File list
        self._file_list._screen_rect = Rect(sr.x + 2, sr.y + 5, sr.width - 6, sr.height - 11)
        self._file_list.paint(painter)

        # Filename input
        fname_y = sr.y + sr.height - 5
        painter.put_str(lx + 2, fname_y - sr.y + ly, "File:", fg=fg, bg=bg, attrs=Attrs.BOLD)
        self._filename_input._screen_rect = Rect(sr.x + 2, fname_y + 1, sr.width - 6, 1)
        self._filename_input.paint(painter)

        # Buttons
        btn_y = sr.y + sr.height - 3
        self._ok_btn._screen_rect = Rect(sr.x + sr.width - 24, btn_y, 10, 1)
        self._cancel_btn._screen_rect = Rect(sr.x + sr.width - 13, btn_y, 10, 1)
        self._ok_btn.paint(painter)
        self._cancel_btn.paint(painter)

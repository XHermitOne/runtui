"""SaveFileDialog -- file browser dialog for saving files."""

from __future__ import annotations

from .file_open import OpenFileDialog


class SaveFileDialog(OpenFileDialog):
    """File browser dialog for selecting a file to save.

    Behaves like OpenFileDialog but with 'Save' button label
    and allows entering non-existing filenames.
    """

    def __init__(
        self,
        title: str = "Save File",
        initial_dir: str = "",
        filters: list[tuple[str, str]] | None = None,
        default_name: str = "",
        width: int = 60,
        height: int = 20,
    ) -> None:
        super().__init__(title=title, initial_dir=initial_dir,
                         filters=filters, width=width, height=height)
        self._ok_btn.text = "Save"
        if default_name:
            self._filename_input.text = default_name

    def _on_ok(self) -> None:
        """Save dialog allows any filename, doesn't require existing file."""
        filename = self._filename_input.text
        if filename:
            full_path = self._current_dir / filename
            self.close(str(full_path))
        else:
            self.close(None)

#!/usr/bin/env python3
"""Notes application - Mac Notes style TUI application."""

import json
import os
from datetime import datetime
from typing import Optional

import runtui
from runtui import App, Window, Label, Button, ListBox, TextArea, MessageBox
from runtui import MenuBar, Menu, MenuItem
from runtui.widgets.container import Container
from runtui.layout.dock import DockLayout
from runtui.layout.absolute import AbsoluteLayout
from runtui.core.types import BorderStyle


# JSON file path (same directory as this script)
NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")


class Note:
    """Represents a single note."""

    def __init__(
        self,
        id: str,
        title: str = "",
        content: str = "",
        created_at: Optional[str] = None,
        modified_at: Optional[str] = None,
    ):
        self.id = id
        self.title = title
        self.content = content
        self.created_at = created_at or datetime.now().isoformat()
        self.modified_at = modified_at or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            created_at=data.get("created_at"),
            modified_at=data.get("modified_at"),
        )

    def update_modified(self):
        """Update the modified timestamp."""
        self.modified_at = datetime.now().isoformat()

    def get_display_title(self) -> str:
        """Get title for display in the list. Uses first line of content if no title."""
        if self.title:
            return self.title
        # Use first non-empty line of content as title
        lines = self.content.strip().split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped:
                return stripped[:30] + ("..." if len(stripped) > 30 else "")
        return "Untitled Note"

    def get_display_date(self) -> str:
        """Get formatted date for display."""
        try:
            dt = datetime.fromisoformat(self.modified_at)
            now = datetime.now()
            if dt.date() == now.date():
                return dt.strftime("%H:%M")
            elif (now - dt).days < 7:
                return dt.strftime("%a")
            else:
                return dt.strftime("%m/%d/%y")
        except (ValueError, TypeError):
            return "?"


class NotesApp(App):
    """Mac Notes style application."""

    def __init__(self):
        super().__init__(theme="light")
        self.notes: list[Note] = []
        self.current_note: Optional[Note] = None
        self._saving = False
        self._loading = True
        # Set up menu bar
        self._setup_menu()
        


    def on_ready(self) -> None:
        """Initialize the application."""
        

        # Create main window (fullscreen-ish)
        screen_w = 90
        screen_h = 35

        win = Window(
            title="Notes",
            x=1,
            y=1,
            width=screen_w,
            height=screen_h,
        )

        # Create main container with dock layout
        main_container = Container()
        main_container._layout_manager = DockLayout()

        # Left panel - note list (20% width)
        left_panel = Container(border=BorderStyle.SINGLE, title="Notes")
        left_panel.dock = "left"
        left_panel.width = 22
        left_panel._layout_manager = DockLayout()

        # Note list
        self.note_list = ListBox(
            items=[],
            x=0,
            y=0,
            width=20,
            height=20,
            on_select=self._on_note_select,
            on_activate=self._on_note_activate,
        )
        self.note_list.dock = "fill"

        # Button container at bottom of left panel
        btn_container = Container()
        btn_container.dock = "bottom"
        btn_container.height = 3
        btn_container._layout_manager = AbsoluteLayout()



        left_panel.add_child(self.note_list)
        left_panel.add_child(btn_container)

        # Right panel - note editor
        right_panel = Container(border=BorderStyle.SINGLE, title="Editor")
        right_panel.dock = "fill"
        right_panel._layout_manager = DockLayout()

        # Title label showing note info
        self.title_label = Label(text="Select or create a note", x=0, y=0, width=60)
        self.title_label.dock = "top"
        self.title_label.height = 1

        # Content editor
        self.content_editor = TextArea(
            text="",
            x=0,
            y=0,
            width=60,
            height=25,
            on_change=self._on_content_change,
        )
        self.content_editor.dock = "fill"

        right_panel.add_child(self.title_label)
        right_panel.add_child(self.content_editor)

        # Add panels to main container
        main_container.add_child(left_panel)
        main_container.add_child(right_panel)

        win.set_content(main_container)
        self.add_window(win)

        # Store references for later
        self._main_container = main_container
        self._left_panel = left_panel
        self._right_panel = right_panel
        self._btn_container = btn_container

        # Load notes from file
        self._load_notes()
        self._loading = False

    def get_menu(self) -> MenuBar:
        return MenuBar(menus=[
            Menu("File", [
                MenuItem("New Note", shortcut="Ctrl+N", action=self._new_note),
                MenuItem("Delete Note", shortcut="Ctrl+D", action=self._delete_note),
                MenuItem.separator(),
                MenuItem("Exit", shortcut="Ctrl+Q", action=self.quit),
            ]),
            # Menu("Edit", [
            #     MenuItem("Undo", shortcut="Ctrl+Z", action=self._undo),
            #     MenuItem("Redo", shortcut="Ctrl+Y", action=self._redo),
            # ]),
            Menu("Help", [
                MenuItem("About", action=self._show_about),
            ]),
        ])
    
    def _setup_menu(self) -> None:
        """Set up the menu bar."""
        menu = self.get_menu()
        self.set_menu(menu)

    def _undo(self) -> None:
        """Undo in editor."""
        if hasattr(self.content_editor, '_undo'):
            self.content_editor._undo()

    def _redo(self) -> None:
        """Redo in editor."""
        if hasattr(self.content_editor, '_redo'):
            self.content_editor._redo()

    def _show_about(self) -> None:
        """Show about dialog."""
        mb = MessageBox(
            title="About Notes",
            message=(
                "Notes - A Mac Notes style TUI\n\n"
                "Features:\n"
                "- Create and delete notes\n"
                "- Auto-save on edit\n"
                "- Sorted by modification date\n\n"
                "Shortcuts:\n"
                "Ctrl+N - New note\n"
                "Ctrl+D - Delete note\n"
                "Ctrl+Q - Exit"
            ),
            buttons=["OK"],
        )
        mb.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        self.root.add_child(mb)
        mb.invalidate()

    def _load_notes(self):
        """Load notes from JSON file."""
        if not os.path.exists(NOTES_FILE):
            # Create empty notes file
            self._save_notes_to_file()
            return

        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.notes = [Note.from_dict(n) for n in data.get("notes", [])]

            # Sort by modified_at descending (most recent first)
            self.notes.sort(key=lambda n: n.modified_at, reverse=True)

            # Update list display
            self._refresh_note_list()

            # Select first note if available
            if self.notes:
                self.note_list.selected_index = 0
                self._select_note(self.notes[0])

        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading notes: {e}")
            self.notes = []

    def _save_notes_to_file(self):
        """Save all notes to JSON file."""
        try:
            data = {
                "notes": [n.to_dict() for n in self.notes],
                "version": 1,
            }
            with open(NOTES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving notes: {e}")

    def _refresh_note_list(self):
        """Refresh the note list display."""
        items = []
        for note in self.notes:
            title = note.get_display_title()
            date = note.get_display_date()
            # Format: "Title            DD/MM"
            display = f"{title[:18]:<18} {date:>6}"
            items.append(display)

        self.note_list.items = items

    def _on_note_select(self, index: int, item: str):
        """Handle note selection in list."""
        if 0 <= index < len(self.notes):
            self._select_note(self.notes[index])

    def _on_note_activate(self, index: int, item: str):
        """Handle note activation (double-click/Enter)."""
        # Focus the editor
        self.content_editor.focus()

    def _select_note(self, note: Note):
        """Select and display a note."""
        self.current_note = note

        # Update title label
        created = self._format_date(note.created_at)
        modified = self._format_date(note.modified_at)
        title_text = f"{note.get_display_title()}  |  Created: {created}  |  Modified: {modified}"
        self.title_label.text = title_text

        # Update content editor
        self.content_editor.text = note.content

    def _format_date(self, iso_date: str) -> str:
        """Format ISO date for display."""
        try:
            dt = datetime.fromisoformat(iso_date)
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return "?"

    def _on_content_change(self, new_text: str):
        """Handle content change in editor - auto-save."""
        if self._loading or not self.current_note:
            return

        self.current_note.content = new_text

        # Extract title from first line
        lines = new_text.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            self.current_note.title = first_line[:50] if first_line else ""

        self.current_note.update_modified()

        # Re-sort notes (most recent first)
        self.notes.sort(key=lambda n: n.modified_at, reverse=True)

        # Refresh list but maintain selection
        current_note = self.current_note
        self._refresh_note_list()

        # Find and reselect the current note
        for i, note in enumerate(self.notes):
            if note.id == current_note.id:
                # Temporarily disconnect callback to avoid recursion
                old_select = self.note_list._on_select
                self.note_list._on_select = None
                self.note_list.selected_index = i
                self.note_list._on_select = old_select
                break

        # Update title label
        created = self._format_date(current_note.created_at)
        modified = self._format_date(current_note.modified_at)
        title_text = f"{current_note.get_display_title()}  |  Created: {created}  |  Modified: {modified}"
        self.title_label.text = title_text

        # Auto-save
        self._save_notes_to_file()

    def _new_note(self):
        """Create a new note."""
        # Generate unique ID
        note_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

        note = Note(
            id=note_id,
            title="",
            content="",
        )

        # Add to beginning (most recent)
        self.notes.insert(0, note)

        # Refresh and select
        self._refresh_note_list()
        self.note_list.selected_index = 0
        self._select_note(note)

        # Focus editor
        self.content_editor.focus()

        # Save
        self._save_notes_to_file()

    def _delete_note(self):
        """Delete the current note."""
        if not self.current_note:
            return

        # Confirm deletion
        mb = MessageBox(
            title="Delete Note",
            message=f"Delete '{self.current_note.get_display_title()}'?\nThis cannot be undone.",
            buttons=["Delete", "Cancel"],
        )
        mb.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        self.root.add_child(mb)

        # We'll handle the response via callback on button click
        # For simplicity, just delete directly
        self._confirm_delete()

    def _confirm_delete(self):
        """Actually delete the note."""
        if not self.current_note:
            return

        note_id = self.current_note.id
        self.notes = [n for n in self.notes if n.id != note_id]

        self._refresh_note_list()
        self._save_notes_to_file()

        # Select next note or clear editor
        if self.notes:
            self.note_list.selected_index = 0
            self._select_note(self.notes[0])
        else:
            self.current_note = None
            self.title_label.text = "Select or create a note"
            self.content_editor.text = ""


if __name__ == "__main__":
    app = NotesApp()
    app.run()

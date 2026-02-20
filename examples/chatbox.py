#!/usr/bin/env python3
"""
LLM Chat Application - OpenWebUI style TUI.
Requires the 'runtui' library as defined in the provided sample.
"""

import json
import os
import threading
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any

# We assume runtui is installed or available in the path as per your sample
import runtui
from runtui import App, Window, Label, Button, ListBox, TextArea, MessageBox
from runtui import MenuBar, Menu, MenuItem
from runtui.widgets.container import Container
from runtui.widgets.input import TextInput
from runtui.dialogs.base import Dialog
from runtui.layout.dock import DockLayout
from runtui.layout.absolute import AbsoluteLayout
from runtui.core.types import Attrs, BorderStyle, Color, Rect
from runtui.rendering.painter import Painter

# File Paths
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CONVERSATIONS_FILE = os.path.join(DATA_DIR, "conversations.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


# --- Data Models ---

class AppSettings:
    """Manages LLM configuration."""
    def __init__(self):
        self.provider = "ollama"  # ollama, openai, claude, etc.
        self.base_url = "http://localhost:11434/v1"
        self.api_key = ""
        self.model = "gpt-oss:20b"
        self.temperature = 0.7
        self.max_tokens = 2048

    def to_dict(self) -> dict:
        return self.__dict__

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        settings = cls()
        if data:
            for k, v in data.items():
                if hasattr(settings, k):
                    setattr(settings, k, v)
        return settings


class Message:
    """A single chat message."""
    def __init__(self, role: str, content: str):
        self.role = role  # 'user' or 'assistant' or 'system'
        self.content = content
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        msg = cls(role=data.get("role", "user"), content=data.get("content", ""))
        msg.timestamp = data.get("timestamp", datetime.now().isoformat())
        return msg


class Conversation:
    """Represents a chat session."""
    def __init__(self, id: str, title: str = "New Chat"):
        self.id = id
        self.title = title
        self.messages: List[Message] = []
        self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()
        self.model_used = ""

    def update_modified(self):
        self.modified_at = datetime.now().isoformat()

    def add_message(self, role: str, content: str):
        self.messages.append(Message(role, content))
        self.update_modified()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "model_used": self.model_used
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        conv = cls(id=data.get("id"), title=data.get("title", "New Chat"))
        conv.created_at = data.get("created_at")
        conv.modified_at = data.get("modified_at")
        conv.model_used = data.get("model_used", "")
        conv.messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return conv

    def get_display_date(self) -> str:
        try:
            dt = datetime.fromisoformat(self.modified_at)
            now = datetime.now()
            if dt.date() == now.date():
                return dt.strftime("%H:%M")
            elif (now - dt).days < 7:
                return dt.strftime("%a")
            else:
                return dt.strftime("%m/%d")
        except:
            return "?"


# --- Logic / Backend ---

class LLMClient:
    """Handles API communication."""
    
    @staticmethod
    def chat_completion(settings: AppSettings, messages: List[Dict]) -> str:
        """Synchronous call to LLM API (OpenAI compatible)."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.api_key}"
        }
        
        payload = {
            "model": settings.model,
            "messages": messages,
            "temperature": float(settings.temperature),
            "max_tokens": int(settings.max_tokens),
            "stream": False 
        }

        try:
            # Handle Ollama vs OpenAI base URLs
            url = settings.base_url.rstrip('/')
            if "chat/completions" not in url:
                url += "/chat/completions"

            response = requests.post(url, headers=headers, json=payload, timeout=180)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            return f"[Error: {str(e)}]"

    @staticmethod
    def generate_title(settings: AppSettings, conversation_text: str) -> str:
        """Ask LLM to summarize the conversation into a title."""
        prompt = [
            {"role": "system", "content": "Summarize the following conversation into a short title (max 5 words). Do not use quotes."},
            {"role": "user", "content": conversation_text[:1000]} # Limit context
        ]
        return LLMClient.chat_completion(settings, prompt).strip()


# --- Custom UI Widgets ---

class SettingsDialog(Dialog):
    """Modal dialog for configuring LLM settings."""

    FIELDS = [
        ("provider", "Provider", "ollama, openai, claude"),
        ("base_url", "Base URL", "http://localhost:11434/v1"),
        ("api_key", "API Key", "leave empty for Ollama"),
        ("model", "Model Name", "gpt-oss:20b, gpt-4o"),
        ("temperature", "Temperature", "0.0 to 1.0"),
        ("max_tokens", "Max Tokens", "e.g. 2048"),
    ]

    def __init__(self, app_ref, current_settings: AppSettings):
        height = len(self.FIELDS) * 2 + 7
        super().__init__(title="LLM Configuration", width=60, height=height)
        self.app_ref = app_ref
        self.settings = current_settings

        self.inputs = {}
        for key, label_text, placeholder in self.FIELDS:
            val = str(getattr(self.settings, key))
            inp = TextInput(text=val, placeholder=placeholder, width=34)
            self.inputs[key] = inp
            self.add_child(inp)

        self._save_btn = Button(text="Save", on_click=self._save)
        self._cancel_btn = Button(text="Cancel", on_click=lambda: self.close(None))
        self.add_child(self._save_btn)
        self.add_child(self._cancel_btn)

    def paint(self, painter: Painter) -> None:
        super().paint(painter)

        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("dialog.bg", Color.BRIGHT_BLACK)
        fg = self.theme_color("dialog.fg", Color.BLACK)

        label_w = 14
        y = ly + 2
        for key, label_text, _ in self.FIELDS:
            painter.put_str(lx + 2, y, label_text + ":", fg=fg, bg=bg, attrs=Attrs.BOLD)
            widget = self.inputs[key]
            widget._screen_rect = Rect(sr.x + label_w + 4, sr.y + (y - ly), 34, 1)
            widget.paint(painter)
            y += 2

        self._save_btn._screen_rect = Rect(sr.x + sr.width - 24, sr.y + sr.height - 3, 10, 1)
        self._cancel_btn._screen_rect = Rect(sr.x + sr.width - 13, sr.y + sr.height - 3, 10, 1)
        self._save_btn.paint(painter)
        self._cancel_btn.paint(painter)

    def _save(self):
        try:
            self.settings.provider = self.inputs['provider'].text.strip()
            self.settings.base_url = self.inputs['base_url'].text.strip()
            self.settings.api_key = self.inputs['api_key'].text.strip()
            self.settings.model = self.inputs['model'].text.strip()
            self.settings.temperature = float(self.inputs['temperature'].text.strip())
            self.settings.max_tokens = int(self.inputs['max_tokens'].text.strip())

            self.app_ref.save_settings(self.settings)
            self.close("saved")
            self.app_ref.show_message("Settings Saved", "Configuration updated successfully.")
        except ValueError:
            self.app_ref.show_message("Error", "Invalid number format for Temperature or Max Tokens.")


class RenameDialog(Dialog):
    """Modal dialog for renaming a conversation."""

    def __init__(self, current_title: str, on_rename):
        super().__init__(title="Rename Conversation", width=50, height=9)
        self._on_rename = on_rename

        self._input = TextInput(text=current_title, width=38)
        self.add_child(self._input)

        self._ok_btn = Button(text="OK", on_click=self._do_rename)
        self._cancel_btn = Button(text="Cancel", on_click=lambda: self.close(None))
        self.add_child(self._ok_btn)
        self.add_child(self._cancel_btn)

    def paint(self, painter: Painter) -> None:
        super().paint(painter)

        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y

        bg = self.theme_color("dialog.bg", Color.BRIGHT_BLACK)
        fg = self.theme_color("dialog.fg", Color.BLACK)

        painter.put_str(lx + 2, ly + 2, "Title:", fg=fg, bg=bg, attrs=Attrs.BOLD)
        self._input._screen_rect = Rect(sr.x + 9, sr.y + 2, 38, 1)
        self._input.paint(painter)

        self._ok_btn._screen_rect = Rect(sr.x + sr.width - 24, sr.y + sr.height - 3, 10, 1)
        self._cancel_btn._screen_rect = Rect(sr.x + sr.width - 13, sr.y + sr.height - 3, 10, 1)
        self._ok_btn.paint(painter)
        self._cancel_btn.paint(painter)

    def _do_rename(self):
        new_title = self._input.text.strip()
        if new_title:
            self._on_rename(new_title)
        self.close(new_title)


# --- Main Application ---

class ChatApp(App):
    """OpenWebUI-like TUI Chat."""

    def __init__(self):
        super().__init__(theme="dark")
        self.conversations: List[Conversation] = []
        self.current_conv: Optional[Conversation] = None
        self.settings = AppSettings()

    def on_ready(self) -> None:
        """Initialize UI."""
        self._setup_menu()

        # Load Data
        self._load_settings()
        self._load_conversations()

        # --- Main Window ---
        screen_w = 100
        screen_h = 36

        win = Window(title="TUI Chat (LLM)", x=0, y=0, width=screen_w, height=screen_h)

        # Main Layout
        main_container = Container()
        main_container._layout_manager = DockLayout()

        # --- Left Panel (Sidebar) ---
        left_panel = Container(border=BorderStyle.SINGLE, title="Chats")
        left_panel.dock = "left"
        left_panel.width = 25
        left_panel._layout_manager = DockLayout()

        # New Chat Button
        new_chat_btn = Button(text="+ New Chat", x=0, y=0, width=20, on_click=self._new_chat)
        new_chat_btn.dock = "top"
        new_chat_btn.height = 3

        # Conversation List
        self.conv_list = ListBox(
            items=[],
            x=0, y=0, width=20, height=20,
            on_select=self._on_conv_select
        )
        self.conv_list.dock = "fill"

        left_panel.add_child(new_chat_btn)
        left_panel.add_child(self.conv_list)

        # --- Right Panel (Chat Area) ---
        right_panel = Container(border=BorderStyle.SINGLE, title="Conversation")
        right_panel.dock = "fill"
        right_panel._layout_manager = DockLayout()

        # Header Info
        self.header_label = Label(text="Model: Not Configured", x=0, y=0, width=60)
        self.header_label.dock = "top"
        self.header_label.height = 1

        # Chat History (Read Only Output with scrollbar)
        self.history_display = TextArea(text="", x=0, y=0, width=60, height=20, readonly=True)
        self.history_display.dock = "fill"

        # Input Area Container
        input_container = Container()
        input_container.dock = "bottom"
        input_container.height = 8 # Enough for multi-line
        input_container._layout_manager = DockLayout()

        # Send Button container (Right side of input)
        btn_area = Container()
        btn_area.dock = "right"
        btn_area.width = 12
        btn_area._layout_manager = AbsoluteLayout()
        
        self.send_btn = Button(text="SEND >", x=1, y=2, width=10, on_click=self._on_send_msg)
        btn_area.add_child(self.send_btn)

        # Input Text Area
        self.input_box = TextArea(text="", x=0, y=0, width=50, height=5)
        self.input_box.dock = "fill"

        input_container.add_child(btn_area)
        input_container.add_child(self.input_box)

        right_panel.add_child(self.header_label)
        right_panel.add_child(input_container) # Bottom docked
        right_panel.add_child(self.history_display) # Fill rest

        main_container.add_child(left_panel)
        main_container.add_child(right_panel)

        win.set_content(main_container)
        self.add_window(win)

        self._refresh_conv_list()
        self._update_header()
        
        # If no conversations, create one
        if not self.conversations:
            self._new_chat()
        else:
            self.conv_list.selected_index = 0
            self._on_conv_select(0, "")


    # --- Menu & Configuration ---

    def get_menu(self) -> MenuBar:
        return MenuBar(menus=[
            Menu("File", [
                MenuItem("New Chat", shortcut="Ctrl+N", action=self._new_chat),
                MenuItem("Rename Chat", action=self._rename_chat),
                MenuItem("Delete Chat", shortcut="Ctrl+D", action=self._delete_chat),
                MenuItem("Exit", shortcut="Ctrl+Q", action=self.quit),
            ]),
            Menu("Settings", [
                MenuItem("Configure LLM...", action=self._show_settings),
            ]),
        ])

    def _setup_menu(self):
        self.set_menu(self.get_menu())

    def _show_settings(self):
        """Open settings modal dialog."""
        sw = SettingsDialog(self, self.settings)
        sw.center_on_screen(100, 40)
        self.root.add_child(sw)
        self._needs_repaint = True

    def save_settings(self, new_settings: AppSettings):
        self.settings = new_settings
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings.to_dict(), f, indent=2)
        except IOError as e:
            self.show_message("Error", f"Failed to save settings: {e}")
        self._update_header()

    def _load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    self.settings = AppSettings.from_dict(json.load(f))
            except:
                pass

    def _update_header(self):
        if self.current_conv:
            txt = f"[{self.settings.provider}] {self.settings.model} | {self.current_conv.title}"
        else:
            txt = f"[{self.settings.provider}] {self.settings.model}"
        self.header_label.text = txt

    # --- Conversation Logic ---

    def _load_conversations(self):
        if not os.path.exists(CONVERSATIONS_FILE):
            self.conversations = []
            return
        try:
            with open(CONVERSATIONS_FILE, "r") as f:
                data = json.load(f)
                self.conversations = [Conversation.from_dict(c) for c in data]
            # Sort by modified (recent first)
            self.conversations.sort(key=lambda c: c.modified_at, reverse=True)
        except:
            self.conversations = []

    def _save_conversations(self):
        try:
            data = [c.to_dict() for c in self.conversations]
            with open(CONVERSATIONS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            pass

    def _refresh_conv_list(self):
        items = []
        for c in self.conversations:
            title = c.title[:18]
            date = c.get_display_date()
            items.append(f"{title:<18} {date:>5}")
        self.conv_list.items = items

    def _on_conv_select(self, index: int, item: str):
        if 0 <= index < len(self.conversations):
            self.current_conv = self.conversations[index]
            self._render_chat_history()
            self._update_header()

    def _render_chat_history(self):
        if not self.current_conv:
            self.history_display.text = ""
            return
        
        buffer = ""
        for msg in self.current_conv.messages:
            role_display = "USER" if msg.role == "user" else "AI"
            # Simple separator line
            buffer += f"--- {role_display} ---\n{msg.content}\n\n"
        
        self.history_display.text = buffer
        # In a real TUI, we would trigger scroll to bottom here

    def _new_chat(self):
        cid = datetime.now().strftime("%Y%m%d%H%M%S")
        new_conv = Conversation(id=cid)
        self.conversations.insert(0, new_conv)
        self._refresh_conv_list()
        self.conv_list.selected_index = 0
        self._on_conv_select(0, "")
        self.input_box.focus()

    def _delete_chat(self):
        if not self.current_conv:
            return

        self.conversations = [c for c in self.conversations if c.id != self.current_conv.id]
        self.current_conv = None
        self._save_conversations()

        if self.conversations:
            self._refresh_conv_list()
            self.conv_list.selected_index = 0
            self._on_conv_select(0, "")
        else:
            self._new_chat()

    def _rename_chat(self):
        if not self.current_conv:
            return

        def apply_rename(new_title):
            self.current_conv.title = new_title
            self.current_conv.update_modified()
            self._save_conversations()
            self._refresh_conv_list()
            self._update_header()

        dlg = RenameDialog(self.current_conv.title, apply_rename)
        dlg.center_on_screen(100, 40)
        dlg.parent = self.root
        self.root.add_child(dlg)
        self._needs_repaint = True

    # --- Interaction Logic ---

    def _on_send_msg(self):
        """Handle sending a message."""
        text = self.input_box.text.strip()
        if not text or not self.current_conv:
            return

        # Add user message and clear input
        self.current_conv.add_message("user", text)
        self.input_box.text = ""
        self._render_chat_history()

        # Disable send button while waiting
        self.send_btn.text = "Wait.."

        # Trigger LLM call in background thread
        t = threading.Thread(target=self._process_llm_response, args=(text,), daemon=True)
        t.start()

    def _process_llm_response(self, user_text):
        """Background thread for API call."""
        conv = self.current_conv

        # Prepare context (last 10 messages to save tokens)
        msgs_payload = [{"role": m.role, "content": m.content} for m in conv.messages[-10:]]

        # Call API
        response_text = LLMClient.chat_completion(self.settings, msgs_payload)

        # Update Data
        conv.add_message("assistant", response_text)
        conv.model_used = self.settings.model

        # Auto-summarize title on first exchange (user + assistant = 2 messages)
        if len(conv.messages) <= 2:
            try:
                context = f"User: {user_text}\nAI: {response_text}"
                new_title = LLMClient.generate_title(self.settings, context)
                if new_title and "Error" not in new_title:
                    conv.title = new_title
            except:
                pass

        # Re-sort by most recent and persist
        self.conversations.sort(key=lambda c: c.modified_at, reverse=True)
        self._save_conversations()

        # Schedule UI updates on the main thread
        self.call_later(0, self._after_llm_response)

    def _after_llm_response(self):
        """Update UI after LLM response (runs on main thread)."""
        self.send_btn.text = "SEND >"
        self._render_chat_history()
        self._refresh_conv_list()
        self._update_header()

        # Restore selection to current conversation after sort
        for i, c in enumerate(self.conversations):
            if self.current_conv and c.id == self.current_conv.id:
                self.conv_list.selected_index = i
                break

    def close_dialog(self, dialog):
        """Helper to close and remove a dialog."""
        if hasattr(dialog, 'close'):
            dialog.close(None)
        self._needs_repaint = True

    def show_message(self, title, msg):
        mb = MessageBox(title=title, message=msg, buttons=["OK"])
        mb.center_on_screen(100, 40)
        mb.parent = self.root
        self.root.add_child(mb)
        self._needs_repaint = True


if __name__ == "__main__":
    app = ChatApp()
    app.run()
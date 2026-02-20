#!/usr/bin/env python3
"""Key Caps - Virtual keyboard layout display."""

from runtui import App, Window, Label, TextInput, MessageBox
from runtui import MenuBar, Menu, MenuItem
from runtui.widgets.container import Container
from runtui.layout.absolute import AbsoluteLayout
from runtui.core.event import MouseEvent
from runtui.core.keys import MouseAction, MouseButton
from runtui.core.types import Color


# Keyboard layout: each row is a list of (label, width, char_or_action)
# char_or_action: a string to type, or a special action name
KEYBOARD_ROWS = [
    # Row 0: number row
    [
        ("`", 4, "`"), ("1", 4, "1"), ("2", 4, "2"), ("3", 4, "3"),
        ("4", 4, "4"), ("5", 4, "5"), ("6", 4, "6"), ("7", 4, "7"),
        ("8", 4, "8"), ("9", 4, "9"), ("0", 4, "0"), ("-", 4, "-"),
        ("=", 4, "="), ("Bksp", 6, "backspace"),
    ],
    # Row 1: QWERTY row
    [
        ("Tab", 6, "tab"), ("Q", 4, "Q"), ("W", 4, "W"), ("E", 4, "E"),
        ("R", 4, "R"), ("T", 4, "T"), ("Y", 4, "Y"), ("U", 4, "U"),
        ("I", 4, "I"), ("O", 4, "O"), ("P", 4, "P"), ("[", 4, "["),
        ("]", 4, "]"), ("\\", 4, "\\"),
    ],
    # Row 2: home row
    [
        ("Caps", 7, "caps"), ("A", 4, "A"), ("S", 4, "S"), ("D", 4, "D"),
        ("F", 4, "F"), ("G", 4, "G"), ("H", 4, "H"), ("J", 4, "J"),
        ("K", 4, "K"), ("L", 4, "L"), (";", 4, ";"), ("'", 4, "'"),
        ("Ret", 7, "return"),
    ],
    # Row 3: bottom row
    [
        ("Shift", 9, "shift"), ("Z", 4, "Z"), ("X", 4, "X"), ("C", 4, "C"),
        ("V", 4, "V"), ("B", 4, "B"), ("N", 4, "N"), ("M", 4, "M"),
        (",", 4, ","), (".", 4, "."), ("/", 4, "/"), ("Shift", 7, "shift"),
    ],
    # Row 4: space bar
    [
        ("Space", 40, " "),
    ],
]

# Row x-offsets to approximate staggered keyboard layout
ROW_OFFSETS = [0, 0, 1, 2, 8]


class KeyCapsApp(App):
    """Virtual keyboard display application."""

    def __init__(self):
        super().__init__(theme="light")
        self._caps_on = False
        self._shift_on = False
        self._setup_menu()

    def on_ready(self) -> None:
        win = Window(
            title="Key Caps",
            x=5,
            y=2,
            width=64,
            height=14,
        )

        content = Container()
        content._layout_manager = AbsoluteLayout()

        # Text input at top
        self.text_input = TextInput(
            text="",
            placeholder="Click keys below to type...",
            x=1,
            y=0,
            width=60,
        )
        content.add_child(self.text_input)

        # Build keyboard rows using Labels with mouse handlers
        key_y = 2
        for row_idx, row in enumerate(KEYBOARD_ROWS):
            key_x = 1 + ROW_OFFSETS[row_idx]
            for label_text, width, action in row:
                key_label = Label(
                    text=label_text,
                    x=key_x,
                    y=key_y,
                    width=width,
                    height=2,
                    align="center",
                    bg=Color.WHITE,
                    fg=Color.BLACK,
                )
                key_label.can_focus = True

                def make_handler(a=action):
                    def handler(event: MouseEvent):
                        if event.action == MouseAction.RELEASE and event.button == MouseButton.LEFT:
                            self._key_press(a)
                            event.mark_handled()
                    return handler

                key_label.on(MouseEvent, make_handler())
                content.add_child(key_label)
                key_x += width
            key_y += 2

        win.set_content(content)
        self.add_window(win)

    def get_menu(self) -> MenuBar:
        return MenuBar(menus=[
            Menu("File", [
                MenuItem("Clear", shortcut="Ctrl+L", action=self._clear),
                MenuItem.separator(),
                MenuItem("Quit", shortcut="Ctrl+Q", action=self.quit),
            ]),
            Menu("Help", [
                MenuItem("About", action=self._show_about),
            ]),
        ])

    def _setup_menu(self) -> None:
        menu = self.get_menu()
        self.set_menu(menu)

    def _key_press(self, action: str) -> None:
        """Handle a virtual key press."""
        if action == "backspace":
            if self.text_input.text:
                self.text_input.text = self.text_input.text[:-1]
        elif action == "return":
            self.text_input.text += "\n"
        elif action == "tab":
            self.text_input.text += "\t"
        elif action == "caps":
            self._caps_on = not self._caps_on
        elif action == "shift":
            self._shift_on = not self._shift_on
        else:
            char = action
            if len(char) == 1 and char.isalpha():
                if self._caps_on != self._shift_on:
                    char = char.upper()
                else:
                    char = char.lower()
            self.text_input.text += char
            if self._shift_on:
                self._shift_on = False

    def _clear(self) -> None:
        self.text_input.text = ""

    def _show_about(self) -> None:
        mb = MessageBox(
            title="About Key Caps",
            message=(
                "Key Caps\n\n"
                "A virtual keyboard display.\n"
                "Click keys to type characters\n"
                "into the text field above.\n\n"
                "Special keys:\n"
                "Bksp - Delete last character\n"
                "Caps - Toggle caps lock\n"
                "Shift - Shift next character"
            ),
            buttons=["OK"],
        )
        mb.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        self.root.add_child(mb)
        mb.invalidate()


if __name__ == "__main__":
    app = KeyCapsApp()
    app.run()

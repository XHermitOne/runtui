#!/usr/bin/env python3
"""Win Mine - Text UI Minesweeper."""

import random
from runtui import App, Window, Label, MessageBox, Button
from runtui import MenuBar, Menu, MenuItem
from runtui.widgets.container import Container
from runtui.layout.absolute import AbsoluteLayout
from runtui.core.event import MouseEvent
from runtui.core.keys import MouseAction, MouseButton
from runtui.core.types import Color

# Game Constants
GRID_W = 9
GRID_H = 9
NUM_MINES = 10

# Visual Constants
CELL_WIDTH = 4
CELL_HEIGHT = 2
OFFSET_X = 2
OFFSET_Y = 4  # Leave room for header/counters

class Cell:
    """Represents a single cell in the minefield."""
    def __init__(self):
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.neighbor_mines = 0

class WinMineApp(App):
    """Minesweeper Application."""

    def __init__(self):
        super().__init__(theme="light")
        self.grid = []
        self.game_over = False
        self.ui_labels = [] # 2D array of Label widgets
        self.msg_label = None
        self.flag_mode = False # Toggle for terminals without right-click support
        self._setup_menu()

    def on_ready(self) -> None:
        # Calculate window size based on grid
        win_w = (GRID_W * CELL_WIDTH) + 4 + 1
        win_h = (GRID_H * CELL_HEIGHT) + 6 

        win = Window(
            title="Mine",
            x=5,
            y=2,
            width=win_w,
            height=win_h,
        )

        content = Container()
        content._layout_manager = AbsoluteLayout()

        # Status Label (Mines Left / Game Over msg)
        self.msg_label = Label(
            text=f"Mines: {NUM_MINES}",
            x=OFFSET_X,
            y=1,
            width=20,
            height=2,
            fg=Color.BLACK
        )
        content.add_child(self.msg_label)

        # Flag Mode Toggle Button (For accessibility)
        self.mode_btn = Button(
            text="Mode: DIG",
            x=win_w - 16,
            y=1,
            width=12,
            height=2,
        )
        
        def toggle_mode(event: MouseEvent):
            if event.action == MouseAction.RELEASE and event.button == MouseButton.LEFT:
                self.flag_mode = not self.flag_mode
                self.mode_btn.label = "Mode: FLAG" if self.flag_mode else "Mode: DIG"
                event.mark_handled()
        
        self.mode_btn.on(MouseEvent, toggle_mode)
        content.add_child(self.mode_btn)

        # Initialize Logic and UI Grid
        self._init_game_state()
        self._build_grid_ui(content)

        win.set_content(content)
        self.add_window(win)

    def get_menu(self) -> MenuBar:
        return MenuBar(menus=[
            Menu("Game", [
                MenuItem("New Game", shortcut="F2", action=self._reset_game),
                MenuItem.separator(),
                MenuItem("Quit", shortcut="Ctrl+Q", action=self.quit),
            ]),
            Menu("Help", [
                MenuItem("How to Play", action=self._show_help),
            ]),
        ])

    def _setup_menu(self) -> None:
        self.set_menu(self.get_menu())

    def _init_game_state(self):
        """Reset logic board."""
        self.grid = [[Cell() for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.game_over = False
        
        # Place Mines
        mines_placed = 0
        while mines_placed < NUM_MINES:
            rx = random.randint(0, GRID_W - 1)
            ry = random.randint(0, GRID_H - 1)
            if not self.grid[ry][rx].is_mine:
                self.grid[ry][rx].is_mine = True
                mines_placed += 1

        # Calculate Neighbors
        for y in range(GRID_H):
            for x in range(GRID_W):
                if self.grid[y][x].is_mine:
                    continue
                count = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < GRID_H and 0 <= nx < GRID_W:
                            if self.grid[ny][nx].is_mine:
                                count += 1
                self.grid[y][x].neighbor_mines = count

    def _build_grid_ui(self, content: Container):
        """Create the grid of Labels."""
        self.ui_labels = []
        
        current_y = OFFSET_Y
        for y in range(GRID_H):
            row_labels = []
            current_x = OFFSET_X
            for x in range(GRID_W):
                lbl = Label(
                    text="",
                    x=current_x,
                    y=current_y,
                    width=CELL_WIDTH,
                    height=CELL_HEIGHT,
                    align="center",
                    bg=Color.WHITE,
                    fg=Color.BLACK,
                )
                lbl.can_focus = True

                # Create closure for event handler
                def make_handler(bx=x, by=y):
                    def handler(event: MouseEvent):
                        if event.action == MouseAction.RELEASE:
                            # Support Right Click OR Left Click if Flag Mode is on
                            if event.button == MouseButton.RIGHT or (self.flag_mode and event.button == MouseButton.LEFT):
                                self._handle_flag(bx, by)
                            elif event.button == MouseButton.LEFT:
                                self._handle_click(bx, by)
                            event.mark_handled()
                    return handler

                lbl.on(MouseEvent, make_handler())
                content.add_child(lbl)
                row_labels.append(lbl)
                current_x += CELL_WIDTH
            
            self.ui_labels.append(row_labels)
            current_y += CELL_HEIGHT
        
        self._refresh_ui()

    def _handle_click(self, x, y):
        if self.game_over:
            return
            
        cell = self.grid[y][x]
        
        if cell.is_flagged or cell.is_revealed:
            return

        if cell.is_mine:
            self._game_over_loss()
        else:
            self._reveal_recursive(x, y)
            self._check_win()
            self._refresh_ui()

    def _handle_flag(self, x, y):
        if self.game_over:
            return
            
        cell = self.grid[y][x]
        if not cell.is_revealed:
            cell.is_flagged = not cell.is_flagged
            self._refresh_ui()

    def _reveal_recursive(self, x, y):
        """Flood fill for empty spaces."""
        if not (0 <= x < GRID_W and 0 <= y < GRID_H):
            return
        
        cell = self.grid[y][x]
        if cell.is_revealed or cell.is_flagged:
            return
            
        cell.is_revealed = True
        
        if cell.neighbor_mines == 0:
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    self._reveal_recursive(x + dx, y + dy)

    def _check_win(self):
        revealed_count = 0
        for y in range(GRID_H):
            for x in range(GRID_W):
                if self.grid[y][x].is_revealed:
                    revealed_count += 1
        
        target = (GRID_W * GRID_H) - NUM_MINES
        if revealed_count == target:
            self.game_over = True
            self.msg_label.text = "YOU WIN!"
            self.msg_label.fg = Color.BLUE
            self._show_message("Congratulations", "You cleared the minefield!")

    def _game_over_loss(self):
        self.game_over = True
        self.msg_label.text = "BOOM! Game Over"
        self.msg_label.fg = Color.RED
        
        # Reveal all mines
        for y in range(GRID_H):
            for x in range(GRID_W):
                if self.grid[y][x].is_mine:
                    self.grid[y][x].is_revealed = True
        
        self._refresh_ui()
        self._show_message("Game Over", "You hit a mine!")

    def _refresh_ui(self):
        """Syncs the Visual Grid with the Logic Grid."""
        flag_count = 0
        
        for y in range(GRID_H):
            for x in range(GRID_W):
                cell = self.grid[y][x]
                ui_lbl = self.ui_labels[y][x]
                
                if cell.is_flagged:
                    flag_count += 1
                    ui_lbl.text = " 🚩 " # Flag icon representation
                    ui_lbl.fg = Color.RED
                    ui_lbl.bg = Color.WHITE
                elif not cell.is_revealed:
                    ui_lbl.text = "."
                    ui_lbl.fg = Color.BLACK
                    ui_lbl.bg = Color.WHITE
                else:
                    # Revealed
                    if cell.is_mine:
                        ui_lbl.text = "*"
                        ui_lbl.bg = Color.RED
                        ui_lbl.fg = Color.WHITE
                    else:
                        ui_lbl.bg = Color.LIGHT_GRAY if hasattr(Color, 'LIGHT_GRAY') else Color.WHITE
                        if cell.neighbor_mines == 0:
                            ui_lbl.text = " "
                        else:
                            ui_lbl.text = str(cell.neighbor_mines)
                            # Simple color coding
                            if cell.neighbor_mines == 1: ui_lbl.fg = Color.BLUE
                            elif cell.neighbor_mines == 2: ui_lbl.fg = Color.GREEN
                            else: ui_lbl.fg = Color.RED

        if not self.game_over:
            self.msg_label.text = f"Mines: {NUM_MINES - flag_count}"
            self.msg_label.fg = Color.BLACK

    def _reset_game(self) -> None:
        self._init_game_state()
        self._refresh_ui()
        self.msg_label.text = f"Mines: {NUM_MINES}"

    def _show_message(self, title, msg) -> None:
        mb = MessageBox(
            title=title,
            message=msg,
            buttons=["OK"],
        )
        mb.center_on_screen(
            self._screen.width if self._screen else 80,
            self._screen.height if self._screen else 24,
        )
        self.root.add_child(mb)

    def _show_help(self) -> None:
        self._show_message(
            "Controls", 
            "Left Click: Reveal Cell\n"
            "Right Click: Flag Mine\n"
            "(Or use Mode button to toggle Dig/Flag)"
        )

if __name__ == "__main__":
    app = WinMineApp()
    app.run()
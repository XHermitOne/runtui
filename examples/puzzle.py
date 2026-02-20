#!/usr/bin/env python3
"""Puzzle - Classic 4x4 sliding tile puzzle (15-puzzle)."""

import random

from runtui import App, Window, Label, Button, MessageBox
from runtui import MenuBar, Menu, MenuItem
from runtui.widgets.container import Container
from runtui.layout.absolute import AbsoluteLayout
from runtui.core.event import MouseEvent
from runtui.core.keys import MouseAction, MouseButton
from runtui.core.types import Color


class PuzzleApp(App):
    """Classic 15-puzzle sliding tile game."""

    TILE_W = 6
    TILE_H = 2
    GRID_SIZE = 4

    def __init__(self):
        super().__init__(theme="light")
        self.board = list(range(1, 16)) + [0]
        self.moves = 0
        self.tiles = []
        self._setup_menu()

    def on_ready(self) -> None:
        grid_w = self.TILE_W * self.GRID_SIZE + 2
        win_w = grid_w + 4
        win_h = self.TILE_H * self.GRID_SIZE + 7

        win = Window(
            title="Puzzle",
            x=10,
            y=3,
            width=win_w,
            height=win_h,
        )

        content = Container()
        content._layout_manager = AbsoluteLayout()

        # Move counter label at top
        self.move_label = Label(text="Moves: 0", x=1, y=0, width=grid_w)
        content.add_child(self.move_label)

        # Create 4x4 grid of clickable labels
        self.tiles = []
        for row in range(self.GRID_SIZE):
            for col in range(self.GRID_SIZE):
                idx = row * self.GRID_SIZE + col
                bx = 1 + col * self.TILE_W
                by = 2 + row * self.TILE_H
                val = self.board[idx]

                tile = Label(
                    text=str(val) if val != 0 else " ",
                    x=bx,
                    y=by,
                    width=self.TILE_W,
                    height=self.TILE_H,
                    align="center",
                    bg=Color.WHITE,
                    fg=Color.BLACK,
                    bold=True,
                )
                tile.can_focus = True

                def make_handler(i=idx):
                    def handler(event: MouseEvent):
                        if event.action == MouseAction.RELEASE and event.button == MouseButton.LEFT:
                            self._tile_click(i)
                            event.mark_handled()
                    return handler

                tile.on(MouseEvent, make_handler())
                self.tiles.append(tile)
                content.add_child(tile)

        # Status label at bottom
        self.status_label = Label(
            text="Click a tile next to the gap to slide it",
            x=1,
            y=2 + self.GRID_SIZE * self.TILE_H,
            width=grid_w,
        )
        content.add_child(self.status_label)

        win.set_content(content)
        self.add_window(win)

        # Start with a shuffled board
        self._new_game()

    def get_menu(self) -> MenuBar:
        return MenuBar(menus=[
            Menu("Game", [
                MenuItem("New Game", shortcut="Ctrl+N", action=self._new_game),
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

    def _new_game(self) -> None:
        self.board = list(range(1, 16)) + [0]
        self._shuffle()
        self.moves = 0
        self._update_display()
        self.status_label.text = "Shuffled \u2014 slide tiles to solve!"

    def _shuffle(self, num_moves: int = 200) -> None:
        """Shuffle by making random valid moves (guarantees solvability)."""
        empty = self.board.index(0)
        last_move = -1
        for _ in range(num_moves):
            neighbors = self._get_neighbors(empty)
            neighbors = [n for n in neighbors if n != last_move] or neighbors
            swap = random.choice(neighbors)
            self.board[empty], self.board[swap] = self.board[swap], self.board[empty]
            last_move = empty
            empty = swap

    def _get_neighbors(self, idx: int) -> list[int]:
        """Get indices of tiles adjacent to idx."""
        row, col = divmod(idx, self.GRID_SIZE)
        neighbors = []
        if row > 0:
            neighbors.append(idx - self.GRID_SIZE)
        if row < self.GRID_SIZE - 1:
            neighbors.append(idx + self.GRID_SIZE)
        if col > 0:
            neighbors.append(idx - 1)
        if col < self.GRID_SIZE - 1:
            neighbors.append(idx + 1)
        return neighbors

    def _tile_click(self, idx: int) -> None:
        """Handle a tile click -- slide if adjacent to empty."""
        if self.board[idx] == 0:
            return

        empty = self.board.index(0)
        if idx in self._get_neighbors(empty):
            self.board[empty], self.board[idx] = self.board[idx], self.board[empty]
            self.moves += 1
            self._update_display()

            if self._is_solved():
                self.status_label.text = f"Solved in {self.moves} moves!"

    def _is_solved(self) -> bool:
        return self.board == list(range(1, 16)) + [0]

    def _update_display(self) -> None:
        """Update all tile labels and move counter."""
        for i, tile in enumerate(self.tiles):
            val = self.board[i]
            tile.text = str(val) if val != 0 else " "
            if val == 0:
                tile._bg = Color.DEFAULT
                tile.bold = False
            else:
                tile._bg = Color.WHITE
                tile.bold = True
            tile.invalidate()
        self.move_label.text = f"Moves: {self.moves}"

    def _show_about(self) -> None:
        mb = MessageBox(
            title="About Puzzle",
            message=(
                "15-Puzzle\n\n"
                "Slide tiles into the empty space\n"
                "to arrange them 1-15 in order.\n\n"
                "Click a tile adjacent to the\n"
                "gap to move it."
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
    app = PuzzleApp()
    app.run()

# rendering Package

Rendering pipeline for runtui: buffers, screen management, and painter.

## Modules

| Module | Description |
|--------|-------------|
| `buffer` | CellBuffer - 2D grid of terminal cells |
| `screen` | Screen - double buffering and diff-based flush |
| `painter` | Painter - clipped drawing API for widgets |

## Rendering Pipeline

1. Widgets paint to the back buffer via `Painter`
2. `Screen.flush()` compares back buffer vs front buffer
3. Only changed cells are written to the terminal
4. Back buffer is copied to front buffer
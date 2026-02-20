# layout Package

Layout managers for widget positioning.

## Modules

| Module | Description |
|--------|-------------|
| `base` | Abstract base class for layout managers |
| `absolute` | Absolute positioning layout |
| `dock` | Dock layout for edge-docked children |
| `box` | Horizontal and vertical box layouts |
| `grid` | Grid layout with rows and columns |

## Available Layouts

- **AbsoluteLayout**: Children specify their own x, y, width, height
- **DockLayout**: Children dock to top/bottom/left/right/fill
- **HBoxLayout**: Children arranged horizontally (left to right)
- **VBoxLayout**: Children arranged vertically (top to bottom)
- **GridLayout**: Children arranged in a grid
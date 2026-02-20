# backend Package

Terminal backend abstraction layer for cross-platform terminal I/O.

## Modules

| Module | Description |
|--------|-------------|
| `base` | Abstract backend interface |
| `detect` | Platform detection to select the appropriate backend |
| `unix` | Unix (Linux/macOS) terminal backend |
| `windows` | Windows terminal backend |

## Platform Support

The backend automatically detects the platform and selects the appropriate implementation:

- **Unix**: Uses ANSI escape sequences, termios, and select()
- **Windows**: Uses VT100 sequences via Windows Terminal / ConEmu with Win32 Console API fallback
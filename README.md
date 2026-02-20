# RunTUI — Modern Terminal UI Framework for Python

*Build beautiful, interactive, mouse-aware terminal applications in pure Python — no curses, no ncurses, no external dependencies.*

<p align="center">
  <img src="https://github.com/Erickrus/runtui/blob/main/images/demo.gif?raw=true" alt="runtui in action — animated demo">
</p>

`runtui` is a full-featured, cross-platform **TUI (Text User Interface)** library written in **100% pure Python**.  
It brings modern desktop-like experience into your terminal: windows, dialogs, forms, image rendering, embedded terminals, mouse support, theming, layout managers and even a **visual RAD (Rapid Application Development) designer**.

Works seamlessly on **Linux**, **macOS**, and **Windows**

## ✨ Highlights

- Pure Python — zero compiled dependencies
- Cross-platform (Linux, macOS, Windows)
- Rich set of **widgets** — Button, Input, Password, TextArea, Dropdown, ListBox, CheckBox, Radio, Calendar, ColorPicker, ProgressBar, Image, **real Terminal**, etc.
- Multiple **layout** engines: Absolute, Box, Dock, Grid
- Theme engine with built-in themes: Dark, Light, Nord, Solarized, Turbo Vision / Borland style
- Mouse support (click, drag, scroll, hover)
- Window manager with floating & tiled windows + taskbar
- Dialogs: MessageBox, File Open/Save, Custom Forms
- **Visual RAD designer** (`rad_designer.py`) — drag & drop UI building + code generation
- Embedded **terminal** widget with PTY support (run vim, htop, bash, python REPL, … inside your app!)
- Clean event loop, timers, key bindings, context menus

## Installation

```bash
git clone https://github.com/Erickrus/runtui.git
cd runtui
pip install -e .
# or
pip install .
```

More examples in the [`examples/`](examples/) folder:

- `cal.py`               — Calendar
- `calc.py`              — Calculator
- `chatbox.py`           — LLM Chat App
- `clock.py`             — A basic clock program
- `demo_app.py`          — widget showcase
- `mine.py`              - window's mine game
- `notes.py`             — mac os like personal notes
- `rad_designer.py`      — visual designer (very cool!)
- `puzzle.py`            — mac os like puzzle game
- `tui_os.py`            — tui desktop / OS-like interface

It is highly recommended to run everything inside `tui_os.py` by browse these python files in Finder.


## Why choose runtui over other TUI libraries?

| Feature                     | runtui      | Textual     | urwid      | py_cui     | rich + textual |
|-----------------------------|-------------|-------------|------------|------------|----------------|
| Pure Python                 | ✓           | ✓           | ✓          | ✓          | ✓              |
| Cross-platform (good)       | ✓           | ✓           | △          | ✓          | ✓              |
| Mouse support               | ✓           | ✓           | ✗          | ✓          | ✓              |
| Built-in themes             | ✓ (many)    | ✓ (CSS)     | ✗          | ✗          | ✓              |
| Embedded terminal widget    | ✓ (PTY)     | ✗           | ✗          | ✗          | ✗              |
| Visual RAD designer         | ✓           | ✗           | ✗          | ✗          | ✗              |
| Image rendering             | ✓           | ✓           | ✗          | ✗          | ✓              |
| Floating windows + taskbar  | ✓           | △           | ✗          | ✗          | ✗              |
| LLM Chat App                | ✓           | ✗           | ✗          | ✗          | ✗              |


## License

MIT

---

Made with ❤️ in the terminal  
Start building your next TUI masterpiece today!

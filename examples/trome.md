# Trome - Technical Implementation Design

```
████████╗██████╗  ██████╗ ███╗   ███╗███████╗
╚══██╔══╝██╔══██╗██╔═══██╗████╗ ████║██╔════╝
   ██║   ██████╔╝██║   ██║██╔████╔██║█████╗  
   ██║   ██╔══██╗██║   ██║██║╚██╔╝██║██╔══╝  
   ██║   ██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗
   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
```
Trome - a Text UI mirror for Chrome

This document provides implementation-level details for building Trome
using the runtui library. All new code lives in `examples/trome.py`.
The runtui library itself is NOT modified.

<img src="https://github.com/Erickrus/runtui/blob/main/images/trome.gif?raw=true" />

---

# 1. Existing runtui Components Used

## 1.1 StaticImage Widget

`runtui/widgets/static_image.py:26`

- Renders PIL Image using half-block `▄` characters (2 vertical pixels per cell)
- `paint()` at line 122 iterates `h` rows x `w` cols, calling `painter.put_char()`
- `_get_fitted_image()` at line 88 scales image to fit widget, caches result
- `load()` at line 62 accepts a filepath, converts to RGB PIL Image
- Key: `_image` attribute holds the PIL Image directly — we can set it from a CDP screenshot without saving to disk

## 1.2 ImageWidget (for screenshot preview)

`runtui/widgets/image.py:25`

- Interactive version with toolbar, zoom, pan
- Used by `ImageViewerWindow` in `runtui/tui_os.py:914` for the image preview pattern
- We reuse this same pattern: when user clicks screenshot, open a full ImageViewerWindow

## 1.3 Window System

`runtui/windows/window.py:24`

- `content_rect` at line 94 returns interior area (inside 1-cell border)
- `arrange()` at line 111 re-layouts content when window resizes
- `set_content()` at line 103 sets the single content widget
- `min_width=16, min_height=5` at lines 28-29
- Resize handled via `_do_resize()` at line 314

## 1.4 Widget Base

`runtui/widgets/base.py:16`

- `paint()` at line 164 — override for custom rendering
- `hit_test()` at line 258 — deepest widget at screen coords
- `measure()` at line 124 — desired size
- `arrange()` at line 132 — position within rect
- `_screen_rect` at line 63 — absolute position after layout
- `invalidate()` at line 151 — mark for repaint
- EventMixin provides `on()` and `emit()` for event handling

## 1.5 Container

`runtui/widgets/container.py:10`

- `arrange()` at line 41 delegates to layout manager or gives children full content area
- `paint_if_needed()` at line 97 recursively paints children

## 1.6 Label

`runtui/widgets/label.py:11`

- Static text display with fg/bg/bold, alignment
- `text` property setter at line 39 triggers invalidate

## 1.7 Button

`runtui/widgets/button.py:15`

- Renders `[ text ]` format at line 75
- Click handling via `_handle_mouse()` at line 81
- `on_click` callback at line 103

## 1.8 Painter API

`runtui/rendering/painter.py:10`

- `put_char()` at line 40 — single character with fg/bg/attrs
- `put_str()` at line 53 — text string with clipping
- `fill_rect()` at line 80 — fill rectangle area
- All drawing is clipped to the painter's clip region
- Supports `Attrs.UNDERLINE` (`runtui/core/types.py:204`) for link styling

## 1.9 AbsoluteLayout

`runtui/layout/absolute.py:14`

- Children positioned by their own x, y, width, height
- `arrange()` at line 27 offsets children relative to container origin

## 1.10 App Framework

`runtui/app.py:64`

- `call_later()` at line 248 — one-shot timer
- `set_interval()` at line 253 — repeating timer (used for refresh loop)
- `add_window()` at line 217 — add window to manager
- `invalidate_all()` at line 258 — force full repaint

## 1.11 TuiOS Pattern

`runtui/tui_os.py:1091`

- Window wrapper pattern: `FinderWindow`, `TerminalWindow`, `EditorWindow`, `ImageViewerWindow`
- Each wrapper owns a `Window` and provides `get_menu()` — see line 424, 666, 882, 946
- `_listen_window_events()` at line 1431 for menu switching
- `_on_finder_open_file()` at line 1238 for file type dispatch
- `ImageViewerWindow` at line 914 — the exact pattern we reuse for screenshot preview

## 1.12 Color and Attrs

`runtui/core/types.py:122`

- `Color.from_rgb(r, g, b)` at line 131
- `Attrs.UNDERLINE` at line 204 — for link rendering
- `Attrs.BOLD` at line 201

## 1.13 Events

`runtui/core/event.py:54` — KeyEvent
`runtui/core/event.py` — MouseEvent
`runtui/core/keys.py` — Keys enum, MouseAction, MouseButton

---

# 2. ChromeMirrorWidget — The Composite Widget

## 2.1 Design

A new widget subclass defined entirely in `examples/trome.py`.
It inherits from `Widget` (`runtui/widgets/base.py:16`) and composes:

- A screenshot layer (rendered like StaticImage)
- Text overlays (rendered on top by overwriting cells)
- Link regions (text with `Attrs.UNDERLINE`)
- Button regions (text with `[ ]` brackets)

This is NOT a Container with children — it is a single widget with a
custom `paint()` that draws everything in the correct order.

## 2.2 Why a Single Widget

Using a Container + AbsoluteLayout with separate Label children would
require creating/destroying child widgets on every DOM update. A custom
`paint()` is simpler and faster — we just iterate the extracted elements
and draw them directly onto the painter.

## 2.3 Paint Order

```
1. Render screenshot as half-block image (like StaticImage.paint())
2. For each text element: overwrite the corresponding cells with text
3. For each link element: overwrite cells with underlined text
4. For each button element: overwrite cells with [ label ] format
```

## 2.4 Class Skeleton

```python
class ChromeMirrorWidget(Widget):
    def __init__(self, width, height):
        super().__init__(width=width, height=height)
        self.can_focus = True
        self._screenshot: PIL.Image | None = None      # Current page screenshot
        self._elements: list[DOMElement] = []           # Extracted DOM elements
        self._cell_width = 8                            # Pixels per terminal column
        self._cell_height = 16                          # Pixels per terminal row
        self._viewport_w = 640                          # Chrome viewport width
        self._viewport_h = 480                          # Chrome viewport height
        self._scaled_cache = None
        self._cache_key = ()

    def set_screenshot(self, pil_image):
        """Update screenshot from CDP capture."""
        self._screenshot = pil_image
        self._scaled_cache = None
        self.invalidate()

    def set_elements(self, elements):
        """Update DOM element list from CDP extraction."""
        self._elements = elements
        self.invalidate()

    def paint(self, painter):
        # Step 1: render screenshot (half-block, like static_image.py:122)
        # Step 2: overlay text/links/buttons on top

    def _paint_screenshot(self, painter, lx, ly, w, h):
        """Render screenshot using half-block chars."""
        # Same algorithm as runtui/widgets/static_image.py:122-161

    def _paint_text_overlay(self, painter, lx, ly, w, h):
        """Render extracted text elements on top of screenshot."""
        # For each element, convert pixel bbox to cell coords, draw text

    def _pixel_to_cell(self, px, py):
        """Convert pixel coords to terminal cell coords."""
        col = int(px / self._cell_width)
        row = int(py / self._cell_height)
        return col, row

    def _cell_to_pixel(self, col, row):
        """Convert terminal cell coords to pixel coords (for click routing)."""
        px = col * self._cell_width + self._cell_width // 2
        py = row * self._cell_height + self._cell_height // 2
        return px, py
```

## 2.5 Dynamic Sizing

The widget adapts to its container (the Window content area).
When the window is resized:

1. `arrange()` is called with a new Rect (by `Window.arrange()` at `window.py:111`)
2. The widget recalculates how many cells are available
3. The screenshot is re-fitted (cache invalidated)
4. Text overlays are re-mapped to new cell positions

The Chrome viewport stays fixed at 640x480. Only the terminal mapping changes.

**Minimum window size**: We enforce 42x17 (40 content cols + 2 border =
enough for half the viewport width; 15 content rows + 2 border).
Below this, scrolling would be needed but we keep it simple.

---

# 3. DOM Element Model

## 3.1 DOMElement Dataclass

```python
@dataclass
class DOMElement:
    tag: str                    # "p", "a", "button", "img", etc.
    text: str                   # Visible text content
    element_type: str           # "text", "link", "button", "image", "container"
    bbox: tuple[int,int,int,int]  # (x, y, width, height) in pixels
    url: str = ""               # For links
    style: dict = field(default_factory=dict)  # color, font-weight, etc.
    node_id: int = 0            # CDP DOM node ID for interaction
    children: list = field(default_factory=list)
```

## 3.2 Element Type Rendering

| Type      | Rendering                                           | Reference                    |
|-----------|-----------------------------------------------------|------------------------------|
| text      | `painter.put_str()` with theme fg, transparent bg   | `painter.py:53`              |
| link      | `painter.put_str()` with `Attrs.UNDERLINE`          | `types.py:204`               |
| button    | `painter.put_str()` with `[ label ]` format         | `button.py:75` pattern       |
| image     | Keep screenshot pixels (no overlay)                  | `static_image.py:122`        |
| container | Skip (structural only)                               | —                            |

## 3.3 Text Truncation

Uses the same approach as the design doc (trome.md section 12):
- If text exceeds container width in cells, truncate with `...`
- Uses `runtui/core/unicode.py` `truncate_to_width()` function

---

# 4. Chrome DevTools Protocol (CDP) Connection

## 4.1 Library Choice

Use **Playwright** (sync API). The repo already has `.playwright-cli/` present.
Playwright provides:
- Browser launch/connect
- CDP session access
- Screenshot capture as bytes
- DOM evaluation via `page.evaluate()`
- Input dispatch (click, type, scroll)

Fallback: raw websocket CDP if Playwright is not installed.

## 4.2 Connection Flow

```python
class ChromeBridge:
    def __init__(self, url="http://localhost:9222"):
        self._browser = None
        self._page = None

    def connect(self):
        """Connect to running Chrome or launch new instance."""
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.connect_over_cdp(url)
        self._page = self._browser.contexts[0].pages[0]

    def capture_screenshot(self) -> PIL.Image:
        """Capture viewport screenshot as PIL Image."""
        png_bytes = self._page.screenshot(type="png")
        return Image.open(io.BytesIO(png_bytes))

    def extract_elements(self) -> list[DOMElement]:
        """Extract visible DOM elements with bounding boxes."""
        # Uses page.evaluate() with JavaScript to walk visible nodes

    def click_at(self, x: int, y: int):
        """Dispatch click at pixel coordinates."""
        self._page.mouse.click(x, y)

    def scroll(self, delta_x: int, delta_y: int):
        """Dispatch scroll event."""
        self._page.mouse.wheel(delta_x, delta_y)

    def navigate(self, url: str):
        """Navigate to URL."""
        self._page.goto(url)
```

## 4.3 JavaScript DOM Extractor

```javascript
() => {
    const elements = [];
    const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT,
    );
    while (walker.nextNode()) {
        const node = walker.currentNode;
        if (node.nodeType === Node.TEXT_NODE) {
            const range = document.createRange();
            range.selectNodeContents(node);
            const rect = range.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                const parent = node.parentElement;
                const tag = parent ? parent.tagName.toLowerCase() : "";
                const style = parent ? getComputedStyle(parent) : {};
                elements.push({
                    tag: tag,
                    text: node.textContent.trim(),
                    type: parent && parent.tagName === "A" ? "link"
                        : parent && parent.tagName === "BUTTON" ? "button"
                        : "text",
                    bbox: [rect.x, rect.y, rect.width, rect.height],
                    url: parent && parent.href ? parent.href : "",
                    style: {
                        color: style.color || "",
                        fontWeight: style.fontWeight || "",
                        fontSize: style.fontSize || "",
                    }
                });
            }
        }
    }
    return elements;
}
```

---

# 5. Refresh Loop

## 5.1 Timer-Driven Updates

Using `app.set_interval()` (`runtui/app.py:253`):

```python
# Target: 12 FPS (83ms interval), adjustable
self._refresh_handle = app.set_interval(0.083, self._refresh_tick)
```

## 5.2 Refresh Tick

```python
def _refresh_tick(self):
    if not self._bridge or not self._bridge.is_connected():
        return
    try:
        screenshot = self._bridge.capture_screenshot()
        self._mirror_widget.set_screenshot(screenshot)

        elements = self._bridge.extract_elements()
        self._mirror_widget.set_elements(elements)

        self.app._needs_repaint = True
    except Exception:
        pass  # Chrome may have closed
```

## 5.3 Performance Notes

- At 80x30 cells, `paint()` performs ~2400 `put_char()` calls for the screenshot
- The double-buffered diff flush (`runtui/rendering/screen.py`) only sends changed cells
- Screenshot capture via Playwright is ~30-80ms for 640x480
- PIL resize is ~5-10ms with LANCZOS
- Total budget per frame at 12 FPS: ~83ms — achievable
- At 20 FPS (50ms budget): tight but doable if screenshot is cached between frames when unchanged

---

# 6. Input Routing

## 6.1 Mouse Click → Chrome

When user clicks inside ChromeMirrorWidget:

```python
def _handle_mouse(self, event: MouseEvent):
    sr = self._screen_rect
    rx = event.x - sr.x  # Cell coords relative to widget
    ry = event.y - sr.y

    if event.action == MouseAction.PRESS and event.button == MouseButton.LEFT:
        # Convert cell to pixel
        px, py = self._cell_to_pixel(rx, ry)
        # Check if it's a link/button element
        clicked_elem = self._find_element_at(px, py)
        if clicked_elem and clicked_elem.element_type == "link":
            self._bridge.click_at(px, py)
        elif clicked_elem and clicked_elem.element_type == "button":
            self._bridge.click_at(px, py)
        else:
            self._bridge.click_at(px, py)
        event.mark_handled()
```

## 6.2 Keyboard → Chrome

When the mirror widget has focus, forward key events:

```python
def _handle_key(self, event: KeyEvent):
    if not self._focused:
        return
    if event.key == Keys.CHAR and event.char:
        self._bridge.type_text(event.char)
        event.mark_handled()
    elif event.key == Keys.ENTER:
        self._bridge.press_key("Enter")
        event.mark_handled()
    # ... etc for Tab, Backspace, arrows
```

## 6.3 Scroll → Chrome

```python
# Mouse wheel events
if event.button == MouseButton.SCROLL_UP:
    self._bridge.scroll(0, -100)
elif event.button == MouseButton.SCROLL_DOWN:
    self._bridge.scroll(0, 100)
```

---

# 7. Window Wrapper — TromeWindow

## 7.1 Following the TuiOS Pattern

Same pattern as `FinderWindow` (`tui_os.py:251`), `TerminalWindow` (`tui_os.py:625`), etc.

```python
class TromeWindow:
    def __init__(self, app, url=""):
        self.app = app
        self._url = url

        self.window = Window(
            title="Trome - Loading...",
            width=84,    # 80 content + 2 border + 2 shadow
            height=34,   # 30 content + 2 border + 1 url bar + 1 status
            on_close=self._on_close,
        )
        self.window.min_width = 42
        self.window.min_height = 17

        # Build content with dynamic resize (same pattern as tui_os.py:269)
        content = Container()
        trome = self

        def _trome_arrange(rect):
            content._screen_rect = rect
            content.x, content.y = rect.x, rect.y
            content.width, content.height = rect.width, rect.height
            content._needs_layout = False
            cw, ch = rect.width, rect.height
            # URL bar: top row
            trome._url_input.arrange(Rect(rect.x, rect.y, cw, 1))
            # Mirror: middle area
            mirror_h = max(1, ch - 2)
            trome._mirror.arrange(Rect(rect.x, rect.y + 1, cw, mirror_h))
            # Status: bottom row
            trome._status.arrange(Rect(rect.x, rect.y + 1 + mirror_h, cw, 1))

        content.arrange = _trome_arrange

        self._url_input = TextInput(text=url, on_submit=self._on_navigate)
        content.add_child(self._url_input)

        self._mirror = ChromeMirrorWidget(width=80, height=30)
        content.add_child(self._mirror)

        self._status = Label(text=" Connecting...")
        content.add_child(self._status)

        self.window.set_content(content)

        # Start connection
        self._bridge = ChromeBridge()
        self._start_connection()

    def get_menu(self):
        """Menu bar — same pattern as tui_os.py:424"""
        ...
```

## 7.2 Dynamic Resize Behavior

The `_trome_arrange` function (pattern from `tui_os.py:269`) recalculates
child sizes whenever the window is resized. The ChromeMirrorWidget
receives the new size via `arrange()` and invalidates its scaled image cache.

When terminal is larger than 80x30, extra space is filled with black.
When terminal is smaller, the window can be resized smaller and the
screenshot is re-fitted to the smaller area.

---

# 8. Screenshot Preview (Image Viewer Integration)

## 8.1 Following tui_os.py Pattern

When user wants to see the full screenshot, we open an `ImageViewerWindow`
exactly as `tui_os.py:914` does:

```python
def _open_screenshot_preview(self):
    """Save current screenshot to temp file and open ImageViewerWindow."""
    if self._mirror._screenshot:
        import tempfile
        path = tempfile.mktemp(suffix=".png")
        self._mirror._screenshot.save(path)
        # Use same pattern as tui_os.py:1223
        iw = ImageViewerWindow(self.app, path)
        self.app._image_windows.append(iw)
        self.app.add_window(iw.window)
        self.app._listen_window_events(iw.window)
```

---

# 9. File Structure

Everything in a single file: `examples/trome.py`

```
examples/trome.py
    ├── DOMElement          (dataclass)
    ├── ChromeBridge         (CDP connection)
    ├── ChromeMirrorWidget   (composite widget — Widget subclass)
    ├── TromeWindow          (window wrapper)
    └── TromeApp (or integration into TuiOS)
         └── if __name__ == "__main__": standalone launch
```

---

# 10. Dependencies

- **runtui** (no modifications)
- **Pillow** (PIL) — screenshot decoding and scaling
- **pyte** — used by runtui's TerminalWidget (not directly by Trome, but needed by the framework)
- **Google Chrome** or **Chromium** — the browser being mirrored

Trome does NOT require Playwright at runtime. It connects to Chrome's
DevTools Protocol directly using only the Python standard library
(`http.client`, `socket`, `json`). Playwright is listed in the docstring
for historical reasons but the implementation uses a custom minimal
WebSocket client (`_CDPSocket`).

---

# 11. Setup Guide

## 11.1 Python Packages

```bash
pip install Pillow pyte
```

These are the only third-party Python packages Trome needs beyond the
runtui framework itself.

## 11.2 Chrome / Chromium

Trome auto-detects and auto-launches Chrome in headless mode.  You can
also start Chrome manually with the debug port open.

### macOS

Chrome is typically already installed. If not:

```bash
# Option A: Download from https://www.google.com/chrome/
# Option B: Homebrew
brew install --cask google-chrome
```

Trome searches these paths automatically:
- `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- `/Applications/Chromium.app/Contents/MacOS/Chromium`
- `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser`
- `~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`

To start Chrome manually with the debug port:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9222 \
    --user-data-dir=/tmp/trome_chrome_profile \
    --headless=new
```

### Linux

```bash
# Debian / Ubuntu
sudo apt-get update
sudo apt-get install -y google-chrome-stable
# or
sudo apt-get install -y chromium-browser

# Fedora
sudo dnf install chromium

# Arch
sudo pacman -S chromium
```

To start Chrome manually:

```bash
google-chrome --remote-debugging-port=9222 \
    --user-data-dir=/tmp/trome_chrome_profile \
    --headless=new --no-sandbox --disable-gpu
```

### Windows

Install Chrome from https://www.google.com/chrome/ or via:

```powershell
winget install Google.Chrome
```

Trome searches `PROGRAMFILES`, `PROGRAMFILES(X86)`, and `LOCALAPPDATA`
for `Google\Chrome\Application\chrome.exe` automatically.

To start Chrome manually:

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
    --remote-debugging-port=9222 `
    --user-data-dir=%TEMP%\trome_chrome_profile `
    --headless=new
```

## 11.3 Xvfb (Linux headless servers only)

On Linux machines without a display (CI servers, SSH sessions without
X11 forwarding), Chrome's headless mode usually works out of the box.
If it doesn't, install Xvfb as a fallback virtual display:

```bash
# Debian / Ubuntu
sudo apt-get install -y xvfb

# Fedora
sudo dnf install xorg-x11-server-Xvfb

# Arch
sudo pacman -S xorg-server-xvfb
```

Trome detects the absence of `$DISPLAY` and automatically wraps Chrome
with `xvfb-run` when available. No manual configuration is needed.

## 11.4 Fonts (Linux headless servers only)

Chrome needs fonts installed to render web pages. On desktop systems
these are already present. On minimal server / container images, install
a basic font set:

```bash
# Debian / Ubuntu — covers Latin, CJK, emoji
sudo apt-get install -y \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-noto-cjk \
    fontconfig

# Fedora
sudo dnf install \
    liberation-fonts \
    google-noto-emoji-color-fonts \
    google-noto-sans-cjk-fonts

# Arch
sudo pacman -S \
    ttf-liberation \
    noto-fonts-emoji \
    noto-fonts-cjk
```

After installing fonts, rebuild the font cache:

```bash
fc-cache -fv
```

## 11.5 Quick Start (all platforms)

```bash
# 1. Install Python dependencies
pip install Pillow pyte

# 2. Run Trome (Chrome is auto-launched)
python examples/trome.py

# 3. Or open a specific URL
python examples/trome.py https://example.com
```

Trome will:
1. Look for Chrome already running on port 9222
2. If not found, auto-launch Chrome in headless mode with a temporary profile
3. Connect via CDP and start mirroring

When Trome exits, managed Chrome instances are killed automatically.
If Trome connected to an existing Chrome, it detaches cleanly — Chrome
keeps running with all tabs intact.

---

# 12. Summary of What's New vs What's Reused

| Component              | Status       | Reference                          |
|------------------------|--------------|------------------------------------|
| Half-block rendering   | Reused       | `static_image.py:122-161`         |
| Window management      | Reused       | `window.py:24`, `tui_os.py:251`   |
| Dynamic resize layout  | Reused       | `tui_os.py:269` pattern           |
| Image preview          | Reused       | `tui_os.py:914` ImageViewerWindow |
| Menu bar switching     | Reused       | `tui_os.py:1170`                  |
| Mouse/key events       | Reused       | `base.py:258`, `app.py:288`       |
| Timer-driven refresh   | Reused       | `app.py:253` set_interval         |
| ChromeMirrorWidget     | **New**      | Subclass of Widget                 |
| ChromeBridge           | **New**      | Raw CDP via stdlib WebSocket       |
| DOMElement model       | **New**      | Dataclass for extracted nodes      |
| TromeWindow wrapper    | **New**      | Following tui_os.py window pattern |
| Coordinate mapping     | **New**      | pixel_to_cell / cell_to_pixel      |
| JS DOM extractor       | **New**      | Injected via Runtime.evaluate()    |

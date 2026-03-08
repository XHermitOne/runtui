#!/usr/bin/env python3
"""Trome: Chrome-to-TUI Mirror Rendering System.

Mirrors a running Chrome browser window inside a terminal interface using runtui.
The mirrored interface preserves text, links, buttons, images, and layout
while adapting them to terminal display constraints.

Usage (standalone):
    python examples/trome.py [URL]

    Chrome is auto-detected and launched if not already running with a debug
    port.  Supported on macOS, Linux, and Windows.  If Chrome is already
    running with --remote-debugging-port=9222, Trome connects to it instead.

    When Trome exits it detaches cleanly — Chrome keeps running with all
    its tabs intact.

Usage (from TUI-OS):
    Open trome.py from Finder and choose "Run".

Requirements:
    pip install playwright && playwright install chromium
    pip install Pillow
"""

import atexit
import base64
import io
import json
import os
import platform
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import runtui
from runtui import (
    App,
    Window,
    Label,
    Button,
    TextInput,
    Container,
    MenuBar,
    Menu,
    MenuItem,
    MessageBox,
    Color,
    Rect,
    Size,
    WindowAction,
    WindowEvent,
    KeyEvent,
    Keys,
    Modifiers,
)
from runtui.core.event import MouseEvent
from runtui.core.keys import MouseAction as MA, MouseButton
from runtui.core.types import Attrs
from runtui.core.unicode import char_width, string_width, truncate_to_width
from runtui.rendering.painter import Painter
from runtui.widgets.base import Widget
from runtui.widgets.input import TextInput as _BaseTextInput

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ---------------------------------------------------------------------------
#  UrlInput — Visible URL bar with underline + pen icon
# ---------------------------------------------------------------------------

class UrlInput(_BaseTextInput):
    """URL input field styled with underline and a pen icon.

    Overrides paint() to make the input clearly visible:
      - Pen icon (✎) on the left as a visual cue
      - Underline across the full width
      - Distinct colors so it stands out from the background
    Does NOT modify the runtui library.
    """

    # Unicode pen/pencil icon
    PEN = "\u270E"  # ✎ lower right pencil

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width

        if w <= 2:
            return

        # Colors
        if self._focused:
            fg = Color.from_rgb(255, 255, 255)
            bg = Color.from_rgb(50, 50, 90)
            underline_fg = Color.from_rgb(120, 160, 255)
            pen_fg = Color.from_rgb(255, 220, 80)
        else:
            fg = Color.from_rgb(200, 200, 200)
            bg = Color.from_rgb(45, 45, 45)
            underline_fg = Color.from_rgb(100, 100, 100)
            pen_fg = Color.from_rgb(160, 160, 100)

        # Fill background with underline chars to show it's an input field
        # Use underline attribute on spaces for clean look
        for col in range(w):
            painter.put_char(lx + col, ly, " ", fg=underline_fg, bg=bg, attrs=Attrs.UNDERLINE)

        # Draw pen icon on the left
        painter.put_char(lx, ly, self.PEN, fg=pen_fg, bg=bg)

        text_start = 2  # after pen + space
        text_w = w - text_start

        if text_w <= 0:
            return

        # Show placeholder if empty and not focused
        if not self._text and not self._focused:
            placeholder_fg = Color.from_rgb(120, 120, 120)
            painter.put_str(lx + text_start, ly, self.placeholder,
                            fg=placeholder_fg, bg=bg, attrs=Attrs.UNDERLINE,
                            max_width=text_w)
            return

        # Calculate visible portion
        self._ensure_cursor_visible(text_w)
        visible_text = self._text[self._scroll_offset:]

        # Draw text with underline
        col = 0
        for i, ch in enumerate(visible_text):
            if col >= text_w:
                break
            abs_pos = self._scroll_offset + i
            if (self._selection_start >= 0
                    and self._selection_start <= abs_pos < self._selection_end):
                sel_fg = Color.from_rgb(0, 0, 0)
                sel_bg = Color.from_rgb(100, 160, 255)
                painter.put_char(lx + text_start + col, ly, ch, sel_fg, sel_bg,
                                 Attrs.UNDERLINE)
            else:
                painter.put_char(lx + text_start + col, ly, ch, fg, bg,
                                 Attrs.UNDERLINE)
            col += char_width(ch)

        # Draw cursor
        if self._focused:
            cursor_col = self._cursor_display_pos(text_w)
            if 0 <= cursor_col < text_w:
                ch = (self._text[self._cursor_pos]
                      if self._cursor_pos < len(self._text) else " ")
                painter.put_char(lx + text_start + cursor_col, ly, ch,
                                 Color.from_rgb(0, 0, 0),
                                 Color.from_rgb(255, 255, 255),
                                 Attrs.REVERSE)

    def _cursor_display_pos(self, width: int) -> int:
        """Cursor position relative to text area (not pen icon)."""
        return string_width(self._text[self._scroll_offset:self._cursor_pos])


# ---------------------------------------------------------------------------
#  DOM Element Model
# ---------------------------------------------------------------------------

@dataclass
class DOMElement:
    """Represents an extracted DOM element with its bounding box."""
    tag: str = ""
    text: str = ""
    element_type: str = "text"  # "text", "link", "button", "input", "image", "container"
    bbox: tuple = (0, 0, 0, 0)  # (x, y, width, height) in pixels
    url: str = ""
    style: dict = field(default_factory=dict)
    node_id: int = 0
    color: tuple = (255, 255, 255)  # (r, g, b) text color
    full_text: str = ""  # Original full text when this is a split line fragment


# ---------------------------------------------------------------------------
#  Chrome DevTools Protocol Bridge
# ---------------------------------------------------------------------------

# JavaScript to extract visible DOM elements with bounding boxes
_JS_EXTRACT_ELEMENTS = """
(() => {
    const results = [];
    const seen = new Set();

    function walkNode(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            const text = node.textContent.trim();
            if (!text) return;
            const range = document.createRange();
            range.selectNodeContents(node);
            const rects = range.getClientRects();
            if (rects.length === 0) return;

            const parent = node.parentElement;
            if (!parent) return;
            const tag = parent.tagName.toLowerCase();

            // Skip invisible elements
            const style = getComputedStyle(parent);
            if (style.display === 'none' || style.visibility === 'hidden') return;
            if (parseFloat(style.opacity) < 0.1) return;

            // Determine element type
            let elemType = 'text';
            let url = '';
            let checkElem = parent;
            while (checkElem) {
                if (checkElem.tagName === 'A') {
                    elemType = 'link';
                    url = checkElem.href || '';
                    break;
                }
                if (checkElem.tagName === 'BUTTON' ||
                    (checkElem.tagName === 'INPUT' &&
                     (checkElem.type === 'submit' || checkElem.type === 'button'))) {
                    elemType = 'button';
                    break;
                }
                checkElem = checkElem.parentElement;
            }

            // Get color from computed style
            const colorStr = style.color || 'rgb(0,0,0)';
            const colorMatch = colorStr.match(/\\d+/g);
            const color = colorMatch ? colorMatch.slice(0, 3).map(Number) : [0, 0, 0];

            // When text wraps across multiple lines, getClientRects()
            // returns one rect per line.  Split the text proportionally
            // so each line gets only its portion instead of the full text.
            const visibleRects = [];
            for (const rect of rects) {
                if (rect.width < 2 || rect.height < 2) continue;
                if (rect.bottom < 0 || rect.top > window.innerHeight) continue;
                if (rect.right < 0 || rect.left > window.innerWidth) continue;
                visibleRects.push(rect);
            }

            if (visibleRects.length === 0) return;

            if (visibleRects.length === 1) {
                results.push({
                    tag: tag,
                    text: text,
                    type: elemType,
                    bbox: [Math.round(visibleRects[0].x), Math.round(visibleRects[0].y),
                           Math.round(visibleRects[0].width), Math.round(visibleRects[0].height)],
                    url: url,
                    color: color,
                    fontWeight: style.fontWeight,
                    fullText: '',
                });
            } else {
                // Approximate: split text by total width ratio per line
                const totalWidth = visibleRects.reduce((s, r) => s + r.width, 0);
                let charOffset = 0;
                for (let i = 0; i < visibleRects.length; i++) {
                    const rect = visibleRects[i];
                    const ratio = rect.width / totalWidth;
                    let charCount = Math.round(text.length * ratio);
                    // Last rect gets everything remaining
                    if (i === visibleRects.length - 1) {
                        charCount = text.length - charOffset;
                    }
                    const lineText = text.substring(charOffset, charOffset + charCount).trim();
                    charOffset += charCount;
                    if (!lineText) continue;
                    results.push({
                        tag: tag,
                        text: lineText,
                        type: elemType,
                        bbox: [Math.round(rect.x), Math.round(rect.y),
                               Math.round(rect.width), Math.round(rect.height)],
                        url: url,
                        color: color,
                        fontWeight: style.fontWeight,
                        fullText: text,
                    });
                }
            }
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            const elem = node;
            // Detect input fields (text, search, email, password, etc.)
            const isInput = elem.tagName === 'INPUT' && elem.type !== 'hidden';
            const isTextarea = elem.tagName === 'TEXTAREA';
            if (isInput || isTextarea) {
                const rect = elem.getBoundingClientRect();
                if (rect.width > 2 && rect.height > 2) {
                    const style = getComputedStyle(elem);
                    const colorStr = style.color || 'rgb(0,0,0)';
                    const colorMatch = colorStr.match(/\\d+/g);
                    const color = colorMatch ? colorMatch.slice(0, 3).map(Number) : [0, 0, 0];
                    const isBtn = elem.type === 'submit' || elem.type === 'button';
                    results.push({
                        tag: isTextarea ? 'textarea' : 'input',
                        text: elem.value || elem.placeholder || '',
                        type: isBtn ? 'button' : 'input',
                        bbox: [Math.round(rect.x), Math.round(rect.y),
                               Math.round(rect.width), Math.round(rect.height)],
                        url: '',
                        color: color,
                        fontWeight: style.fontWeight,
                    });
                }
            }
            // Also detect contenteditable divs
            if (elem.isContentEditable && elem.getAttribute('contenteditable') === 'true') {
                const rect = elem.getBoundingClientRect();
                if (rect.width > 2 && rect.height > 2) {
                    const style = getComputedStyle(elem);
                    const colorStr = style.color || 'rgb(0,0,0)';
                    const colorMatch = colorStr.match(/\\d+/g);
                    const color = colorMatch ? colorMatch.slice(0, 3).map(Number) : [0, 0, 0];
                    results.push({
                        tag: 'contenteditable',
                        text: elem.innerText.trim().substring(0, 100) || '',
                        type: 'input',
                        bbox: [Math.round(rect.x), Math.round(rect.y),
                               Math.round(rect.width), Math.round(rect.height)],
                        url: '',
                        color: color,
                        fontWeight: style.fontWeight,
                    });
                }
            }
            // Recurse into children
            for (const child of node.childNodes) {
                walkNode(child);
            }
        }
    }

    walkNode(document.body);
    return results;
})()
"""


# ---------------------------------------------------------------------------
#  Cross-Platform Chrome Launcher
# ---------------------------------------------------------------------------

def _find_chrome_executable() -> str | None:
    """Find the Chrome/Chromium executable on this system.

    Search order per platform:
      macOS:   Google Chrome.app, Chromium.app, Brave Browser.app
      Linux:   google-chrome, google-chrome-stable, chromium, chromium-browser
      Windows: Program Files paths, registry fallback
    """
    system = platform.system()

    if system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            os.path.expanduser("~/Applications/Chromium.app/Contents/MacOS/Chromium"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path

    elif system == "Linux":
        candidates = [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "brave-browser",
        ]
        for name in candidates:
            found = shutil.which(name)
            if found:
                return found
        # Also check common install paths
        path_candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ]
        for path in path_candidates:
            if os.path.isfile(path):
                return path

    elif system == "Windows":
        candidates = []
        for env_var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(env_var, "")
            if base:
                candidates.extend([
                    os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                    os.path.join(base, "Chromium", "Application", "chrome.exe"),
                    os.path.join(base, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
                ])
        for path in candidates:
            if os.path.isfile(path):
                return path
        # Try PATH
        found = shutil.which("chrome") or shutil.which("chromium")
        if found:
            return found

    return None


def _is_port_in_use(port: int) -> bool:
    """Check if a TCP port is already listening."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _has_xvfb() -> bool:
    """Check if Xvfb (virtual X server) is available on Linux."""
    return shutil.which("Xvfb") is not None and shutil.which("xvfb-run") is not None


def launch_chrome(port: int = 9222, url: str = "") -> subprocess.Popen | None:
    """Launch Chrome headlessly with remote debugging enabled.

    The browser runs invisibly in the background:
      - macOS/Windows: --headless=new (Chrome's built-in headless mode)
      - Linux: --headless=new, or Xvfb virtual display as fallback

    Returns the Popen handle, or None if Chrome is already running on that
    port or if the executable was not found.
    """
    # If something is already listening on the debug port, don't launch
    if _is_port_in_use(port):
        return None

    chrome_path = _find_chrome_executable()
    if not chrome_path:
        return None

    # Use a dedicated user-data-dir so we don't interfere with the user's
    # normal Chrome profile (which may hold the lock on the debug port).
    user_data_dir = os.path.join(tempfile.gettempdir(), "trome_chrome_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    chrome_args = [
        chrome_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu",
        "--window-size=640,480",
        f"--user-data-dir={user_data_dir}",
    ]
    if url:
        chrome_args.append(url)

    system = platform.system()

    # On Linux without a display, try Xvfb as fallback if headless fails
    use_xvfb = False
    if system == "Linux" and not os.environ.get("DISPLAY") and _has_xvfb():
        use_xvfb = True

    try:
        kwargs: dict[str, Any] = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if system == "Windows":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore
        else:
            kwargs["preexec_fn"] = os.setpgrp

        if use_xvfb:
            # Wrap Chrome in xvfb-run for a virtual display
            args = ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 640x480x24"] + chrome_args
        else:
            args = chrome_args

        proc = subprocess.Popen(args, **kwargs)
        # Give Chrome a moment to start the debug server
        time.sleep(1.5)
        return proc
    except Exception:
        return None


# ---------------------------------------------------------------------------
#  Chrome DevTools Protocol Bridge
# ---------------------------------------------------------------------------

class _CDPSocket:
    """Minimal CDP WebSocket client using only the Python standard library.

    Implements just enough of RFC 6455 to send JSON commands and receive
    JSON responses over Chrome's DevTools Protocol.
    """

    def __init__(self, ws_url: str) -> None:
        import hashlib
        import base64
        import struct
        import socket
        from urllib.parse import urlparse

        parsed = urlparse(ws_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 80
        path = parsed.path or "/"

        self._sock = socket.create_connection((host, port), timeout=10)
        self._sock.settimeout(5)  # 5s timeout for all subsequent recv/send
        self._struct = struct

        # WebSocket handshake
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            f"\r\n"
        )
        self._sock.sendall(handshake.encode())

        # Read handshake response
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket handshake failed")
            resp += chunk

        if b"101" not in resp.split(b"\r\n")[0]:
            raise ConnectionError(f"WebSocket handshake rejected: {resp[:200]}")

        self._id = 0

    def send_command(self, method: str, params: dict | None = None, timeout: float = 5.0) -> dict:
        """Send a CDP command and wait for the response."""
        import socket as _socket
        self._id += 1
        msg = {"id": self._id, "method": method}
        if params:
            msg["params"] = params
        self._send_frame(json.dumps(msg).encode())

        # Read until we get our response (skip events)
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"CDP command {method} timed out after {timeout}s")
            self._sock.settimeout(max(0.1, remaining))
            try:
                data = self._recv_frame()
            except _socket.timeout:
                raise TimeoutError(f"CDP command {method} timed out after {timeout}s")
            parsed = json.loads(data)
            if parsed.get("id") == self._id:
                if "error" in parsed:
                    raise RuntimeError(f"CDP error: {parsed['error']}")
                return parsed.get("result", {})

    def _send_frame(self, data: bytes) -> None:
        """Send a WebSocket text frame (masked, as required by RFC 6455)."""
        import struct
        header = bytearray()
        header.append(0x81)  # FIN + text opcode

        length = len(data)
        if length < 126:
            header.append(0x80 | length)  # MASK bit set
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack(">H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack(">Q", length))

        # Masking key
        mask = os.urandom(4)
        header.extend(mask)

        # Mask the payload
        masked = bytearray(data)
        for i in range(len(masked)):
            masked[i] ^= mask[i % 4]

        self._sock.sendall(bytes(header) + bytes(masked))

    def _recv_frame(self) -> bytes:
        """Receive a complete WebSocket frame."""
        import struct
        import socket as _socket

        def _recv_exact(n: int) -> bytes:
            buf = b""
            while len(buf) < n:
                try:
                    chunk = self._sock.recv(n - len(buf))
                except _socket.timeout:
                    raise
                if not chunk:
                    raise ConnectionError("WebSocket closed")
                buf += chunk
            return buf

        head = _recv_exact(2)
        opcode = head[0] & 0x0F
        masked = (head[1] & 0x80) != 0
        length = head[1] & 0x7F

        if length == 126:
            length = struct.unpack(">H", _recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", _recv_exact(8))[0]

        if masked:
            mask = _recv_exact(4)
            payload = bytearray(_recv_exact(length))
            for i in range(len(payload)):
                payload[i] ^= mask[i % 4]
            return bytes(payload)
        else:
            return _recv_exact(length)

    def close(self) -> None:
        try:
            self._sock.close()
        except Exception:
            pass


class ChromeBridge:
    """Manages connection to Chrome via raw CDP (stdlib only).

    Uses Chrome's HTTP endpoints for discovery and a minimal WebSocket
    client for CDP commands.  No third-party libraries required.
    Playwright is used as an optional enhancement if available.
    """

    def __init__(self):
        self._ws: _CDPSocket | None = None
        self._page_url: str = ""
        self._page_title: str = ""
        self._connected = False
        self._viewport_w = 640
        self._viewport_h = 480
        self._lock = threading.Lock()
        self._chrome_proc: subprocess.Popen | None = None
        self._managed_chrome = False  # True if WE launched Chrome
        self._last_error: str = ""
        self._cdp_base: str = ""

    def connect(self, url: str = "", cdp_url: str = "http://localhost:9222") -> bool:
        """Connect to Chrome. Returns True on success.

        Strategy:
          1. Try connecting to an already-running Chrome debug port.
          2. Auto-launch Chrome with a separate profile and retry.
        """
        import http.client
        from urllib.parse import urlparse

        parsed = urlparse(cdp_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 9222
        self._cdp_base = f"http://{host}:{port}"

        # --- Strategy 1: connect to existing Chrome ---
        # If port is up but has no tabs, create one automatically.
        ws_url = self._discover_page(host, port, create_if_empty=True)

        # If we connected to an existing Chrome that uses our managed
        # profile dir, adopt it so we clean it up on exit.
        if ws_url:
            self._adopt_managed_chrome(port)

        # --- Strategy 2: auto-launch Chrome (managed mode) ---
        if not ws_url:
            self._chrome_proc = launch_chrome(port=port, url=url or "about:blank")
            if self._chrome_proc is not None:
                self._managed_chrome = True
                # Ensure Chrome is killed if the process exits unexpectedly
                atexit.register(self._kill_managed_chrome)
                for _attempt in range(10):
                    time.sleep(0.8)
                    ws_url = self._discover_page(host, port, create_if_empty=True)
                    if ws_url:
                        break

        if not ws_url:
            self._last_error = (
                "Could not connect to Chrome.\n"
                "Start Chrome with:  chrome --remote-debugging-port=9222 "
                "--user-data-dir=/tmp/trome_chrome_profile"
            )
            return False

        # --- Connect WebSocket ---
        try:
            self._ws = _CDPSocket(ws_url)
            self._ws._ws_url = ws_url  # Track which tab we're connected to
        except Exception as e:
            self._last_error = f"WebSocket connection failed: {e}"
            return False

        # Navigate if URL provided and different from current
        if url and url != "about:blank":
            try:
                self._ws.send_command("Page.navigate", {"url": url})
                time.sleep(1.0)  # Let page load
            except Exception:
                pass

        # Enable required CDP domains
        try:
            self._ws.send_command("Page.enable")
            self._ws.send_command("DOM.enable")
            self._ws.send_command("Runtime.enable")
        except Exception:
            pass

        # Prevent target="_blank" links from opening new tabs.
        # Instead, force all navigations into the current tab.
        try:
            self._ws.send_command("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    // Override window.open to navigate in-place
                    window.open = function(url) {
                        if (url) window.location.href = url;
                        return window;
                    };
                    // Rewrite target="_blank" links on click
                    document.addEventListener('click', function(e) {
                        var a = e.target.closest('a');
                        if (a && a.target === '_blank') {
                            e.preventDefault();
                            e.stopPropagation();
                            window.location.href = a.href;
                        }
                    }, true);
                """
            })
        except Exception:
            pass

        # Also apply it to the current page immediately
        try:
            self._ws.send_command("Runtime.evaluate", {
                "expression": """
                    window.open = function(url) {
                        if (url) window.location.href = url;
                        return window;
                    };
                    document.addEventListener('click', function(e) {
                        var a = e.target.closest('a');
                        if (a && a.target === '_blank') {
                            e.preventDefault();
                            e.stopPropagation();
                            window.location.href = a.href;
                        }
                    }, true);
                """
            })
        except Exception:
            pass

        self._connected = True
        return True

    def _discover_page(self, host: str, port: int, create_if_empty: bool = False) -> str | None:
        """Query Chrome's /json/list to find the first page target's wsUrl.

        If create_if_empty is True and the debug port is reachable but has
        no page targets, create a new about:blank tab via /json/new.
        """
        import http.client
        try:
            conn = http.client.HTTPConnection(host, port, timeout=3)
            conn.request("GET", "/json/list")
            resp = conn.getresponse()
            data = json.loads(resp.read().decode())
            conn.close()
            for target in data:
                if target.get("type") == "page":
                    ws = target.get("webSocketDebuggerUrl", "")
                    if ws:
                        # Store page info
                        self._page_url = target.get("url", "")
                        self._page_title = target.get("title", "")
                        return ws

            # Port is reachable but no page targets — create one
            if create_if_empty:
                try:
                    conn2 = http.client.HTTPConnection(host, port, timeout=3)
                    conn2.request("PUT", "/json/new?about:blank")
                    resp2 = conn2.getresponse()
                    new_tab = json.loads(resp2.read().decode())
                    conn2.close()
                    ws = new_tab.get("webSocketDebuggerUrl", "")
                    if ws:
                        self._page_url = new_tab.get("url", "")
                        self._page_title = new_tab.get("title", "")
                        return ws
                except Exception:
                    pass
        except Exception:
            pass
        return None

    def is_connected(self) -> bool:
        return self._connected and self._ws is not None

    def get_url(self) -> str:
        return self._page_url

    def get_title(self) -> str:
        return self._page_title

    def capture_screenshot(self) -> "Image.Image | None":
        """Capture viewport screenshot via CDP Page.captureScreenshot.

        On Retina/HiDPI displays the raw screenshot may be 2x (or more)
        the logical viewport.  We resize it back to the logical size
        so the pixel-to-cell mapping stays consistent.
        """
        if not self.is_connected() or not HAS_PIL:
            return None
        try:
            with self._lock:
                result = self._ws.send_command("Page.captureScreenshot", {
                    "format": "png",
                }, timeout=8)
            png_data = base64.b64decode(result["data"])
            img = Image.open(io.BytesIO(png_data)).convert("RGB")

            # Resize to logical viewport if Retina
            if img.width != self._viewport_w or img.height != self._viewport_h:
                img = img.resize(
                    (self._viewport_w, self._viewport_h), Image.LANCZOS
                )
            return img
        except TimeoutError:
            # Chrome is busy — don't mark as disconnected, just skip this frame
            return None
        except ConnectionError:
            self._connected = False
            self._last_error = "WebSocket disconnected"
            return None
        except Exception as e:
            self._connected = False
            self._last_error = str(e)
            return None

    def extract_elements(self) -> list[DOMElement]:
        """Extract visible DOM elements via CDP Runtime.evaluate."""
        if not self.is_connected():
            return []
        try:
            with self._lock:
                result = self._ws.send_command("Runtime.evaluate", {
                    "expression": _JS_EXTRACT_ELEMENTS.strip(),
                    "returnByValue": True,
                    "timeout": 5000,
                })

            value = result.get("result", {}).get("value", [])
            if not isinstance(value, list):
                return []

            # Also refresh title/url
            try:
                with self._lock:
                    nav = self._ws.send_command("Runtime.evaluate", {
                        "expression": "JSON.stringify({url: location.href, title: document.title})",
                        "returnByValue": True,
                    })
                info = json.loads(nav.get("result", {}).get("value", "{}"))
                self._page_url = info.get("url", self._page_url)
                self._page_title = info.get("title", self._page_title)
            except Exception:
                pass

            elements = []
            for item in value:
                elements.append(DOMElement(
                    tag=item.get("tag", ""),
                    text=item.get("text", ""),
                    element_type=item.get("type", "text"),
                    bbox=tuple(item.get("bbox", [0, 0, 0, 0])),
                    url=item.get("url", ""),
                    color=tuple(item.get("color", [255, 255, 255])),
                    style={"fontWeight": item.get("fontWeight", "")},
                    full_text=item.get("fullText", ""),
                ))
            return elements
        except Exception:
            return []

    def click_at(self, x: int, y: int) -> None:
        """Dispatch mouse click at pixel coordinates via CDP."""
        if not self.is_connected():
            return
        try:
            with self._lock:
                self._ws.send_command("Input.dispatchMouseEvent", {
                    "type": "mousePressed", "x": x, "y": y,
                    "button": "left", "clickCount": 1,
                })
                self._ws.send_command("Input.dispatchMouseEvent", {
                    "type": "mouseReleased", "x": x, "y": y,
                    "button": "left", "clickCount": 1,
                })
        except Exception:
            pass

    def scroll_page(self, delta_x: int, delta_y: int) -> None:
        """Scroll the page via JS window.scrollBy with instant behavior.

        Using Runtime.evaluate instead of Input.dispatchMouseEvent avoids
        Chrome's smooth-scroll animation which causes the page to keep
        moving after the user stops scrolling.
        """
        if not self.is_connected():
            return
        try:
            with self._lock:
                self._ws.send_command("Runtime.evaluate", {
                    "expression": (
                        f"window.scrollBy({{left:{delta_x},top:{delta_y},"
                        f"behavior:'instant'}})"
                    ),
                })
        except Exception:
            pass

    def type_text(self, text: str) -> None:
        """Type text via CDP Input.dispatchKeyEvent."""
        if not self.is_connected():
            return
        try:
            with self._lock:
                for ch in text:
                    self._ws.send_command("Input.dispatchKeyEvent", {
                        "type": "keyDown", "text": ch,
                    })
                    self._ws.send_command("Input.dispatchKeyEvent", {
                        "type": "keyUp", "text": ch,
                    })
        except Exception:
            pass

    def press_key(self, key: str) -> None:
        """Press a special key via CDP."""
        if not self.is_connected():
            return
        # Map Playwright-style key names to CDP key identifiers
        key_map = {
            "Enter": ("\r", "Enter", 13),
            "Tab": ("\t", "Tab", 9),
            "Backspace": ("", "Backspace", 8),
            "Delete": ("", "Delete", 46),
            "Escape": ("", "Escape", 27),
            "ArrowUp": ("", "ArrowUp", 38),
            "ArrowDown": ("", "ArrowDown", 40),
            "ArrowLeft": ("", "ArrowLeft", 37),
            "ArrowRight": ("", "ArrowRight", 39),
            "Home": ("", "Home", 36),
            "End": ("", "End", 35),
            "PageUp": ("", "PageUp", 33),
            "PageDown": ("", "PageDown", 34),
        }
        entry = key_map.get(key)
        if not entry:
            return
        text, key_id, code = entry
        try:
            with self._lock:
                params = {"type": "keyDown", "key": key_id,
                          "windowsVirtualKeyCode": code, "nativeVirtualKeyCode": code}
                if text:
                    params["text"] = text
                self._ws.send_command("Input.dispatchKeyEvent", params)
                params["type"] = "keyUp"
                if "text" in params:
                    del params["text"]
                self._ws.send_command("Input.dispatchKeyEvent", params)
        except Exception:
            pass

    def navigate(self, url: str) -> None:
        """Navigate to URL via CDP."""
        if not self.is_connected():
            return
        try:
            with self._lock:
                self._ws.send_command("Page.navigate", {"url": url})
        except Exception:
            pass

    def check_and_switch_to_new_tab(self) -> bool:
        """Check if Chrome opened a new tab and switch to it.

        Returns True if we switched to a new tab (caller should
        re-inject scripts after the switch).
        """
        import http.client
        from urllib.parse import urlparse

        if not self._cdp_base:
            return False

        try:
            parsed = urlparse(self._cdp_base)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 9222

            conn = http.client.HTTPConnection(host, port, timeout=2)
            conn.request("GET", "/json/list")
            resp = conn.getresponse()
            data = json.loads(resp.read().decode())
            conn.close()

            # Find all page targets
            pages = [t for t in data if t.get("type") == "page"]
            if len(pages) <= 1:
                return False

            # The newest tab is usually last in the list.
            # Find a tab whose wsUrl differs from our current one.
            current_ws = getattr(self._ws, '_ws_url', None)
            for page in reversed(pages):
                ws_url = page.get("webSocketDebuggerUrl", "")
                if ws_url and ws_url != current_ws:
                    # Switch to this new tab
                    try:
                        old_ws = self._ws
                        self._ws = _CDPSocket(ws_url)
                        self._ws._ws_url = ws_url
                        if old_ws:
                            old_ws.close()

                        # Re-enable domains on the new tab
                        self._ws.send_command("Page.enable")
                        self._ws.send_command("DOM.enable")
                        self._ws.send_command("Runtime.enable")

                        # Re-inject the target="_blank" prevention
                        self._inject_no_new_tab_script()

                        self._page_url = page.get("url", "")
                        self._page_title = page.get("title", "")
                        return True
                    except Exception:
                        pass

            return False
        except Exception:
            return False

    def _inject_no_new_tab_script(self) -> None:
        """Inject the script that prevents target=_blank new tabs."""
        script = """
            window.open = function(url) {
                if (url) window.location.href = url;
                return window;
            };
            document.addEventListener('click', function(e) {
                var a = e.target.closest('a');
                if (a && a.target === '_blank') {
                    e.preventDefault();
                    e.stopPropagation();
                    window.location.href = a.href;
                }
            }, true);
        """
        try:
            self._ws.send_command("Page.addScriptToEvaluateOnNewDocument", {
                "source": script
            })
            self._ws.send_command("Runtime.evaluate", {
                "expression": script
            })
        except Exception:
            pass

    def go_back(self) -> None:
        if not self.is_connected():
            return
        try:
            with self._lock:
                # Get navigation history
                result = self._ws.send_command("Page.getNavigationHistory")
                idx = result.get("currentIndex", 0)
                if idx > 0:
                    entries = result.get("entries", [])
                    self._ws.send_command("Page.navigateToHistoryEntry",
                                          {"entryId": entries[idx - 1]["id"]})
        except Exception:
            pass

    def go_forward(self) -> None:
        if not self.is_connected():
            return
        try:
            with self._lock:
                result = self._ws.send_command("Page.getNavigationHistory")
                idx = result.get("currentIndex", 0)
                entries = result.get("entries", [])
                if idx < len(entries) - 1:
                    self._ws.send_command("Page.navigateToHistoryEntry",
                                          {"entryId": entries[idx + 1]["id"]})
        except Exception:
            pass

    def reload(self) -> None:
        if not self.is_connected():
            return
        try:
            with self._lock:
                self._ws.send_command("Page.reload")
        except Exception:
            pass

    def resize_viewport(self, width: int, height: int) -> None:
        """Resize Chrome's viewport via CDP Emulation.setDeviceMetricsOverride.

        This makes Chrome render at the new size, so screenshots and
        DOM element bounding boxes match the terminal widget dimensions.
        """
        if not self.is_connected():
            return
        if width < 64 or height < 48:
            return
        try:
            with self._lock:
                self._ws.send_command("Emulation.setDeviceMetricsOverride", {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 1,
                    "mobile": False,
                })
            self._viewport_w = width
            self._viewport_h = height
        except Exception:
            pass

    def disconnect(self) -> None:
        """Disconnect from Chrome.

        If we launched Chrome ourselves (managed mode), kill the entire
        process tree (Chrome spawns many child processes).
        If we connected to an existing Chrome, just detach — Chrome
        keeps running with all its tabs intact.
        """
        self._connected = False
        if self._ws:
            self._ws.close()
            self._ws = None
        if self._managed_chrome:
            self._kill_managed_chrome()

    def _adopt_managed_chrome(self, port: int) -> None:
        """Check if Chrome on this port uses our managed profile dir.

        If so, adopt it: record its PID so we can kill it on exit.
        """
        try:
            if platform.system() == "Windows":
                # Use wmic to find Chrome with our user-data-dir
                result = subprocess.run(
                    ["wmic", "process", "where",
                     "commandline like '%trome_chrome_profile%'",
                     "get", "processid"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in result.stdout.strip().splitlines():
                    line = line.strip()
                    if line.isdigit():
                        self._managed_pid = int(line)
                        self._managed_chrome = True
                        atexit.register(self._kill_managed_chrome)
                        return
            else:
                # Use ps + grep to find Chrome with our profile dir
                result = subprocess.run(
                    ["pgrep", "-f", "trome_chrome_profile"],
                    capture_output=True, text=True, timeout=5,
                )
                pids = result.stdout.strip().splitlines()
                if pids:
                    # Take the first (main) Chrome process
                    self._managed_pid = int(pids[0])
                    self._managed_chrome = True
                    atexit.register(self._kill_managed_chrome)
        except Exception:
            pass

    def _kill_managed_chrome(self) -> None:
        """Kill the managed Chrome process and all its children."""
        # Determine PID from Popen or adopted PID
        pid = None
        if self._chrome_proc:
            pid = self._chrome_proc.pid
            self._chrome_proc = None
        elif hasattr(self, '_managed_pid') and self._managed_pid:
            pid = self._managed_pid
            self._managed_pid = None

        if pid is None:
            return
        self._managed_chrome = False

        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            else:
                # Try killing the process group first (covers child processes)
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except (ProcessLookupError, PermissionError, OSError):
                    # Fallback: kill just the PID
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except ProcessLookupError:
                        return
                # Wait, then force-kill if needed
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    try:
                        os.kill(pid, 0)  # Check if still alive
                        time.sleep(0.2)
                    except ProcessLookupError:
                        return  # Dead, good
                # Still alive — force kill
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
        except Exception:
            pass


# ---------------------------------------------------------------------------
#  ChromeMirrorWidget — Composite Widget
# ---------------------------------------------------------------------------

class ChromeMirrorWidget(Widget):
    """Composite widget that renders a Chrome page as a terminal mirror.

    Layer 1: Screenshot rendered as half-block image (like StaticImage)
    Layer 2: Text overlays drawn on top of the screenshot

    Inherits from Widget (runtui/widgets/base.py:16).
    Does NOT modify the runtui library.
    """

    def __init__(
        self,
        width: int = 80,
        height: int = 30,
        x: int = 0,
        y: int = 0,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height)
        self.can_focus = True

        # Screenshot state
        self._screenshot: "Image.Image | None" = None
        self._scaled_cache: "Image.Image | None" = None
        self._cache_key: tuple = ()

        # DOM elements overlay
        self._elements: list[DOMElement] = []

        # Coordinate mapping
        self._cell_width = 8    # pixels per terminal column
        self._cell_height = 16  # pixels per terminal row
        self._viewport_w = 640
        self._viewport_h = 480

        # Interaction callbacks
        self._on_click_pixel: Any = None  # (px, py) -> None
        self._on_scroll: Any = None       # (dx, dy) -> None
        self._on_key: Any = None          # (key_str) -> None
        self._on_hover: Any = None        # (elem_or_none) -> None

        # Register event handlers
        self.on(MouseEvent, self._handle_mouse)
        self.on(KeyEvent, self._handle_key_event)

    # --- Public API ---

    def set_screenshot(self, pil_image: "Image.Image") -> None:
        """Update screenshot from CDP capture."""
        self._screenshot = pil_image
        self._scaled_cache = None
        self._cache_key = ()
        self.invalidate()

    def set_elements(self, elements: list[DOMElement]) -> None:
        """Update DOM element list from CDP extraction."""
        self._elements = elements
        self.invalidate()

    # --- Coordinate Mapping ---

    def _pixel_to_cell(self, px: int, py: int, view_w: int, view_h: int) -> tuple:
        """Convert pixel coords to terminal cell coords relative to widget."""
        if self._viewport_w <= 0 or self._viewport_h <= 0:
            return 0, 0
        col = int(px * view_w / self._viewport_w)
        row = int(py * view_h / self._viewport_h)  # each cell = 2 pixels vertically in image
        return max(0, min(col, view_w - 1)), max(0, min(row, view_h - 1))

    def _cell_to_pixel(self, col: int, row: int, view_w: int, view_h: int) -> tuple:
        """Convert terminal cell coords to pixel coords in viewport."""
        if view_w <= 0 or view_h <= 0:
            return 0, 0
        px = int(col * self._viewport_w / view_w)
        py = int(row * self._viewport_h / view_h)
        return px, py

    # --- Rendering ---

    def _get_fitted_screenshot(self, view_w: int, view_h_pixels: int) -> "Image.Image | None":
        """Scale screenshot to fit widget area, cached."""
        if not self._screenshot or not HAS_PIL:
            return None

        key = (self._screenshot.size, view_w, view_h_pixels)
        if self._cache_key == key and self._scaled_cache is not None:
            return self._scaled_cache

        img = self._screenshot
        img_w, img_h = img.size

        # Scale to fit
        zoom_w = view_w / img_w if img_w > 0 else 1.0
        zoom_h = view_h_pixels / img_h if img_h > 0 else 1.0
        zoom = min(zoom_w, zoom_h)

        scaled_w = max(1, int(img_w * zoom))
        scaled_h = max(1, int(img_h * zoom))

        resample = Image.NEAREST if zoom > 2.0 else Image.LANCZOS
        scaled = img.resize((scaled_w, scaled_h), resample)

        # Center on black canvas
        canvas = Image.new("RGB", (view_w, view_h_pixels), (0, 0, 0))
        paste_x = (view_w - scaled_w) // 2
        paste_y = (view_h_pixels - scaled_h) // 2
        canvas.paste(scaled, (paste_x, paste_y))

        self._scaled_cache = canvas
        self._cache_key = key
        return canvas

    def measure(self, available: Size) -> Size:
        return Size(self.width or available.width, self.height or available.height)

    def paint(self, painter: Painter) -> None:
        sr = self._screen_rect
        lx = sr.x - painter._offset.x
        ly = sr.y - painter._offset.y
        w = sr.width
        h = sr.height

        if w <= 0 or h <= 0:
            return

        black = Color.from_rgb(0, 0, 0)

        # Fill background
        painter.fill_rect(lx, ly, w, h, bg=black)

        if not self._screenshot or not HAS_PIL:
            fg = Color.from_rgb(160, 160, 160)
            dim = Color.from_rgb(90, 90, 90)
            if not HAS_PIL:
                msg = "Pillow not installed: pip install Pillow"
            elif not self._screenshot:
                msg = "Connecting to Chrome..."
            else:
                msg = "Waiting for screenshot..."
            cy = ly + h // 2 - 1
            cx = lx + max(0, w // 2 - len(msg) // 2)
            painter.put_str(cx, cy, msg, fg=fg, bg=black)
            hint1 = "Type a URL in the address bar above"
            hint2 = "and press Enter to start browsing"
            painter.put_str(lx + max(0, w // 2 - len(hint1) // 2), cy + 2, hint1, fg=dim, bg=black)
            painter.put_str(lx + max(0, w // 2 - len(hint2) // 2), cy + 3, hint2, fg=dim, bg=black)
            return

        # Layer 1: Render screenshot using half-block characters
        # Same algorithm as runtui/widgets/static_image.py:122-161
        view_h_pixels = h * 2
        canvas_img = self._get_fitted_screenshot(w, view_h_pixels)
        if not canvas_img:
            return

        pixels = canvas_img.load()

        for row in range(h):
            top_py = row * 2
            bot_py = row * 2 + 1
            for col in range(w):
                tr, tg, tb = pixels[col, top_py]
                if bot_py < view_h_pixels:
                    br, bg_r, bb = pixels[col, bot_py]
                else:
                    br, bg_r, bb = 0, 0, 0
                fg = Color.from_rgb(br, bg_r, bb)
                bg = Color.from_rgb(tr, tg, tb)
                painter.put_char(lx + col, ly + row, "▄", fg, bg)

        # Layer 2: Text overlays
        self._paint_text_overlays(painter, lx, ly, w, h)

    def _paint_text_overlays(self, painter: Painter, lx: int, ly: int, w: int, h: int) -> None:
        """Render extracted text elements on top of the screenshot."""
        if not self._elements:
            return

        for elem in self._elements:
            bx, by, bw, bh = elem.bbox

            # Use vertical center of bbox for row placement.
            # HTML elements have padding/line-height so text sits in the
            # middle of the bounding box, not at the top edge.
            center_y = by + bh // 2
            cell_x, cell_y = self._pixel_to_cell(bx, center_y, w, h)
            cell_x2, _ = self._pixel_to_cell(bx + bw, center_y, w, h)
            cell_w = max(1, cell_x2 - cell_x)

            # Skip elements outside visible area
            if cell_y < 0 or cell_y >= h or cell_x >= w:
                continue

            avail_w = min(cell_w, w - cell_x)
            if avail_w <= 0:
                continue

            # --- Input fields: ALWAYS render, even when empty ---
            if elem.element_type == "input":
                self._paint_input_field(painter, lx, ly, cell_x, cell_y, avail_w, elem)
                continue

            text = elem.text
            if not text:
                continue

            if string_width(text) > avail_w:
                text = truncate_to_width(text, avail_w)

            # Determine text color
            r, g, b = elem.color
            fg = Color.from_rgb(r, g, b)

            # Get approximate background color from the screenshot
            bg = Color.from_rgb(0, 0, 0)
            if self._scaled_cache:
                try:
                    px_y = min(cell_y * 2, self._scaled_cache.size[1] - 1)
                    px_x = min(cell_x, self._scaled_cache.size[0] - 1)
                    if px_x >= 0 and px_y >= 0:
                        sr_pixels = self._scaled_cache.load()
                        br, bg_g, bb = sr_pixels[px_x, px_y]
                        bg = Color.from_rgb(br, bg_g, bb)
                except Exception:
                    pass

            if elem.element_type == "link":
                if r + g + b < 200:
                    fg = Color.from_rgb(100, 149, 237)
                painter.put_str(lx + cell_x, ly + cell_y, text, fg=fg, bg=bg, attrs=Attrs.UNDERLINE, max_width=avail_w)

            elif elem.element_type == "button":
                btn_text = f"[{text}]"
                if string_width(btn_text) > avail_w:
                    btn_text = truncate_to_width(btn_text, avail_w)
                btn_fg = Color.from_rgb(255, 255, 255)
                btn_bg = Color.from_rgb(60, 60, 60)
                painter.put_str(lx + cell_x, ly + cell_y, btn_text, fg=btn_fg, bg=btn_bg, attrs=Attrs.BOLD, max_width=avail_w)

            else:
                is_bold = elem.style.get("fontWeight", "") in ("bold", "700", "800", "900")
                attrs = Attrs.BOLD if is_bold else Attrs.NONE
                painter.put_str(lx + cell_x, ly + cell_y, text, fg=fg, bg=bg, attrs=attrs, max_width=avail_w)

    def _paint_input_field(self, painter: Painter, lx: int, ly: int,
                           cell_x: int, cell_y: int, avail_w: int,
                           elem: DOMElement) -> None:
        """Render an input field overlapping the exact Chrome input position.

        Samples bg color from the screenshot so it blends with the page.
        Uses UNDERLINE attribute on spaces (like link style) to indicate
        the input area, with a ✎ pen icon at the start.
        """
        x0 = lx + cell_x
        y0 = ly + cell_y
        text = elem.text

        # Sample bg color from the screenshot at this cell
        bg = Color.from_rgb(255, 255, 255)
        if self._scaled_cache:
            try:
                px_y = max(0, min(cell_y * 2, self._scaled_cache.size[1] - 1))
                px_x = max(0, min(cell_x, self._scaled_cache.size[0] - 1))
                sr_pixels = self._scaled_cache.load()
                br, bg_g, bb = sr_pixels[px_x, px_y]
                bg = Color.from_rgb(br, bg_g, bb)
            except Exception:
                pass

        # Text color from the element
        r, g, b = elem.color
        fg = Color.from_rgb(r, g, b)

        # Pen icon color
        pen_fg = Color.from_rgb(200, 160, 40)

        # Underline indicator color (muted)
        ul_fg = Color.from_rgb(
            max(r - 40, 100), max(g - 40, 100), max(b - 40, 100)
        )

        # Pen icon at position 0
        painter.put_char(x0, y0, "\u270E", fg=pen_fg, bg=bg)

        # Content from position 1 onward
        content_w = avail_w - 1
        if content_w <= 0:
            return

        if text:
            display = truncate_to_width(text, content_w)
            tw = string_width(display)
            painter.put_str(x0 + 1, y0, display, fg=fg, bg=bg, max_width=content_w)
            # Remaining: underlined spaces (like empty link style)
            for c in range(tw, content_w):
                painter.put_char(x0 + 1 + c, y0, " ", fg=ul_fg, bg=bg,
                                 attrs=Attrs.UNDERLINE)
        else:
            # Empty input: all underlined spaces
            for c in range(content_w):
                painter.put_char(x0 + 1 + c, y0, " ", fg=ul_fg, bg=bg,
                                 attrs=Attrs.UNDERLINE)

    # --- Input Handling ---

    def _handle_mouse(self, event: MouseEvent) -> None:
        sr = self._screen_rect
        rx = event.x - sr.x
        ry = event.y - sr.y
        w = sr.width
        h = sr.height

        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            self.focus()
            # Convert cell to pixel coords
            px, py = self._cell_to_pixel(rx, ry, w, h)
            if self._on_click_pixel:
                self._on_click_pixel(px, py)
            event.mark_handled()

        elif event.action == MA.PRESS and event.button == MouseButton.SCROLL_UP:
            if self._on_scroll:
                # Shift+scroll = horizontal (Linux/Windows)
                # Alt+scroll = horizontal (macOS, where Apple Terminal eats Shift+scroll)
                if Modifiers.SHIFT in event.modifiers or Modifiers.ALT in event.modifiers:
                    self._on_scroll(-40, 0)
                else:
                    self._on_scroll(0, -40)
            event.mark_handled()

        elif event.action == MA.PRESS and event.button == MouseButton.SCROLL_DOWN:
            if self._on_scroll:
                if Modifiers.SHIFT in event.modifiers or Modifiers.ALT in event.modifiers:
                    self._on_scroll(40, 0)
                else:
                    self._on_scroll(0, 40)
            event.mark_handled()

        elif event.action == MA.MOVE:
            # Hover: show full text of element under cursor in status bar
            if self._on_hover:
                px, py = self._cell_to_pixel(rx, ry, w, h)
                elem = self._find_element_at(px, py)
                self._on_hover(elem)

    def _handle_key_event(self, event: KeyEvent) -> None:
        if not self._focused:
            return
        if not self._on_key:
            return

        key_map = {
            Keys.ENTER: "Enter",
            Keys.TAB: "Tab",
            Keys.BACKSPACE: "Backspace",
            Keys.DELETE: "Delete",
            Keys.ESCAPE: "Escape",
            Keys.UP: "ArrowUp",
            Keys.DOWN: "ArrowDown",
            Keys.LEFT: "ArrowLeft",
            Keys.RIGHT: "ArrowRight",
            Keys.HOME: "Home",
            Keys.END: "End",
            Keys.PAGE_UP: "PageUp",
            Keys.PAGE_DOWN: "PageDown",
        }

        # Shift+Arrow = horizontal/vertical scroll in the Chrome page
        if Modifiers.SHIFT in event.modifiers and self._on_scroll:
            if event.key == Keys.LEFT:
                self._on_scroll(-40, 0)
                event.mark_handled()
                return
            elif event.key == Keys.RIGHT:
                self._on_scroll(40, 0)
                event.mark_handled()
                return
            elif event.key == Keys.UP:
                self._on_scroll(0, -40)
                event.mark_handled()
                return
            elif event.key == Keys.DOWN:
                self._on_scroll(0, 40)
                event.mark_handled()
                return

        if event.key == Keys.CHAR and event.char:
            self._on_key("char", event.char)
            event.mark_handled()
        elif event.key in key_map:
            self._on_key("special", key_map[event.key])
            event.mark_handled()

    def _find_element_at(self, px: int, py: int) -> DOMElement | None:
        """Find the DOM element at the given pixel coordinates."""
        for elem in reversed(self._elements):
            bx, by, bw, bh = elem.bbox
            if bx <= px < bx + bw and by <= py < by + bh:
                return elem
        return None


# ---------------------------------------------------------------------------
#  TromeWindow — Window Wrapper
# ---------------------------------------------------------------------------

class TromeWindow:
    """Creates and manages a Trome browser mirror window.

    Follows the same wrapper pattern as FinderWindow (tui_os.py:251),
    TerminalWindow (tui_os.py:625), etc.
    """

    def __init__(self, app: "TromeApp", url: str = "") -> None:
        self.app = app
        self._url = url or "about:blank"
        self._bridge = ChromeBridge()
        self._refresh_active = False

        self.window = Window(
            title="Trome",
            width=84,
            height=34,
            on_close=self._on_close,
        )
        self.window.min_width = 42
        self.window.min_height = 17

        # Build content with dynamic resize layout
        # Same pattern as tui_os.py:269 (_finder_arrange)
        content = Container()
        trome = self
        # Track last mirror size so we know when to resize Chrome's viewport
        self._last_mirror_w = 0
        self._last_mirror_h = 0

        def _trome_arrange(rect: Rect) -> None:
            content._screen_rect = rect
            content.x = rect.x
            content.y = rect.y
            content.width = rect.width
            content.height = rect.height
            content._needs_layout = False

            cw = rect.width
            ch = rect.height

            # Row 0: Navigation bar  [<] [>] [R] [H] URL: [________________]
            trome._back_btn.arrange(Rect(rect.x, rect.y, 5, 1))
            trome._fwd_btn.arrange(Rect(rect.x + 5, rect.y, 5, 1))
            trome._reload_btn.arrange(Rect(rect.x + 10, rect.y, 5, 1))
            trome._home_btn.arrange(Rect(rect.x + 15, rect.y, 5, 1))
            trome._url_label.arrange(Rect(rect.x + 20, rect.y, 5, 1))
            trome._url_input.arrange(Rect(rect.x + 25, rect.y, max(1, cw - 25), 1))
            # Rows 1..(ch-2): Mirror widget
            mirror_h = max(1, ch - 2)
            trome._mirror.arrange(Rect(rect.x, rect.y + 1, cw, mirror_h))
            # Bottom row: Status bar
            trome._status.arrange(Rect(rect.x, rect.y + 1 + mirror_h, cw, 1))

            # Detect mirror size change → resize Chrome viewport
            if cw != trome._last_mirror_w or mirror_h != trome._last_mirror_h:
                trome._last_mirror_w = cw
                trome._last_mirror_h = mirror_h
                trome._on_mirror_resized(cw, mirror_h)

        content.arrange = _trome_arrange

        # Navigation buttons
        self._back_btn = Button(text="\u25C0", width=5, on_click=self._go_back)
        content.add_child(self._back_btn)

        self._fwd_btn = Button(text="\u25B6", width=5, on_click=self._go_forward)
        content.add_child(self._fwd_btn)

        self._reload_btn = Button(text="\u21BB", width=5, on_click=self._reload)
        content.add_child(self._reload_btn)

        self._home_btn = Button(text="\u2302", width=5, on_click=self._go_home)
        content.add_child(self._home_btn)

        # URL label
        self._url_label = Label(
            text=" URL:", width=5,
            fg=Color.from_rgb(200, 200, 200),
            bg=Color.from_rgb(60, 60, 60),
            bold=True,
        )
        content.add_child(self._url_label)

        # URL input bar
        self._url_input = TextInput(
            text=self._url if self._url != "about:blank" else "",
            placeholder="Enter URL and press Enter...",
            x=20, y=0, width=60,
            on_submit=self._on_url_submit,
        )
        content.add_child(self._url_input)

        # Mirror widget — the composite rendering area
        self._mirror = ChromeMirrorWidget(width=80, height=30)
        self._mirror._on_click_pixel = self._on_mirror_click
        self._mirror._on_scroll = self._on_mirror_scroll
        self._mirror._on_key = self._on_mirror_key
        self._mirror._on_hover = self._on_mirror_hover
        self._hover_url = ""  # Track current hover URL for status bar
        content.add_child(self._mirror)

        # Status bar
        self._status = Label(
            text=" Click the URL bar above and type an address to browse",
            x=0, y=32, width=80,
            fg=Color.from_rgb(180, 180, 180),
            bg=Color.from_rgb(40, 40, 40),
        )
        content.add_child(self._status)

        self.window.set_content(content)

        # Start connection in background
        self._connect_thread = threading.Thread(target=self._connect_bg, daemon=True)
        self._connect_thread.start()

    # --- Connection ---

    def _connect_bg(self) -> None:
        """Connect to Chrome in a background thread.

        Playwright sync API runs its own event loop internally, so this
        is safe to call from a daemon thread.
        """
        try:
            success = self._bridge.connect(url=self._url)
        except Exception as e:
            self._bridge._last_error = str(e)
            success = False

        if success:
            if self.app and hasattr(self.app, 'call_later'):
                self.app.call_later(0.0, self._on_connected)
        else:
            if self.app and hasattr(self.app, 'call_later'):
                self.app.call_later(0.0, self._on_connect_failed)

    def _on_connected(self) -> None:
        """Called on main thread after successful connection."""
        title = self._bridge.get_title() or "Trome"
        url = self._bridge.get_url()
        self.window.title = f"Trome - {title}" if title else "Trome"
        self._status.text = " Connected | Enter a URL above to start browsing"
        if url and url != "about:blank":
            self._url_input.text = url
            self._status.text = f" {url}"
        self._refresh_active = True
        self.app._needs_repaint = True

        # Command queue: main thread -> refresh thread (click, navigate, etc.)
        self._cmd_queue: queue.Queue = queue.Queue()
        # Update queue: refresh thread -> main thread (screenshots, elements)
        self._update_queue: queue.Queue = queue.Queue()

        # Start the refresh thread — all CDP I/O happens here
        self._refresh_thread = threading.Thread(
            target=self._refresh_loop, daemon=True
        )
        self._refresh_thread.start()

    def _on_connect_failed(self) -> None:
        """Called on main thread after connection failure."""
        self.window.title = "Trome - Connection Failed"
        err = getattr(self._bridge, '_last_error', 'Unknown error')
        self._status.text = f" Failed: {err}"
        self.app._needs_repaint = True

    # --- Command Queue (main thread -> refresh thread) ---

    def _enqueue_cmd(self, cmd: str, *args) -> None:
        """Queue a command for the refresh thread to execute."""
        if hasattr(self, '_cmd_queue'):
            self._cmd_queue.put((cmd, args))

    def _drain_commands(self) -> None:
        """Execute all queued commands (called from refresh thread).

        Scroll commands are coalesced: multiple rapid scroll events are
        merged into a single CDP dispatch to prevent Chrome's smooth
        scrolling from accumulating momentum and overshooting.

        Navigation commands (navigate, back, forward, reload, home) are
        deduplicated: only the LAST navigation command in the batch is
        executed, since earlier ones would be immediately superseded.
        """
        # Drain all pending commands, coalescing scroll deltas
        _NAV_CMDS = {"navigate", "back", "forward", "reload"}
        _RESIZE_CMD = "resize"
        commands: list[tuple[str, tuple]] = []
        scroll_dx = 0
        scroll_dy = 0
        while True:
            try:
                cmd, args = self._cmd_queue.get_nowait()
            except queue.Empty:
                break
            if cmd == "scroll":
                scroll_dx += args[0]
                scroll_dy += args[1]
            else:
                # Flush accumulated scroll before a non-scroll command
                if scroll_dx or scroll_dy:
                    commands.append(("scroll", (scroll_dx, scroll_dy)))
                    scroll_dx = 0
                    scroll_dy = 0
                # If this is a nav command, remove any earlier nav commands
                # since only the last one matters
                if cmd in _NAV_CMDS:
                    commands = [(c, a) for c, a in commands if c not in _NAV_CMDS]
                # Only keep the latest resize command
                if cmd == _RESIZE_CMD:
                    commands = [(c, a) for c, a in commands if c != _RESIZE_CMD]
                commands.append((cmd, args))

        # Flush any remaining scroll
        if scroll_dx or scroll_dy:
            commands.append(("scroll", (scroll_dx, scroll_dy)))

        # Execute coalesced commands
        for cmd, args in commands:
            try:
                if cmd == "navigate":
                    self._bridge.navigate(args[0])
                elif cmd == "click":
                    self._bridge.click_at(args[0], args[1])
                elif cmd == "scroll":
                    self._bridge.scroll_page(args[0], args[1])
                elif cmd == "type":
                    self._bridge.type_text(args[0])
                elif cmd == "press":
                    self._bridge.press_key(args[0])
                elif cmd == "back":
                    self._bridge.go_back()
                elif cmd == "forward":
                    self._bridge.go_forward()
                elif cmd == "reload":
                    self._bridge.reload()
                elif cmd == "resize":
                    self._bridge.resize_viewport(args[0], args[1])
            except (TimeoutError, ConnectionError):
                # CDP timed out or disconnected — skip remaining commands
                break
            except Exception:
                pass

    # --- Refresh Loop (background thread) ---

    def _refresh_loop(self) -> None:
        """Background thread: capture screenshots and process commands.

        All CDP websocket I/O happens exclusively in this thread.
        Results are pushed to the main thread via _update_queue.
        The main thread's _tick() (set_interval) drains the queue.
        """
        frame_count = 0
        consecutive_failures = 0
        while self._refresh_active and self._bridge.is_connected():
            try:
                # Process any queued commands first
                self._drain_commands()

                # Every ~24 frames (~2 seconds), check if Chrome opened
                # a new tab (e.g. from target="_blank" that slipped through)
                # and switch our CDP connection to it.
                frame_count += 1
                if frame_count % 24 == 0:
                    try:
                        self._bridge.check_and_switch_to_new_tab()
                    except Exception:
                        pass

                # Capture screenshot
                screenshot = self._bridge.capture_screenshot()
                elements = self._bridge.extract_elements()
                title = self._bridge.get_title() or "Trome"
                url = self._bridge.get_url()

                # Push update to the thread-safe queue
                # Drop stale frames — only keep the latest
                while not self._update_queue.empty():
                    try:
                        self._update_queue.get_nowait()
                    except queue.Empty:
                        break
                self._update_queue.put((screenshot, elements, title, url))
                consecutive_failures = 0

            except TimeoutError:
                # CDP command timed out — Chrome is busy (navigating/loading).
                # Back off slightly but keep running.
                consecutive_failures += 1
                time.sleep(min(0.5, 0.1 * consecutive_failures))
                continue
            except ConnectionError:
                # WebSocket disconnected — stop the loop
                break
            except Exception:
                consecutive_failures += 1
                if consecutive_failures > 20:
                    break

            # ~12 FPS
            time.sleep(0.083)

    def drain_updates(self) -> None:
        """Drain the update queue on the main thread. Called by TromeApp._tick()."""
        if not hasattr(self, '_update_queue'):
            return
        try:
            screenshot, elements, title, url = self._update_queue.get_nowait()
        except queue.Empty:
            return

        if not self._refresh_active:
            return
        # Sync viewport dimensions from bridge (may have been resized)
        self._mirror._viewport_w = self._bridge._viewport_w
        self._mirror._viewport_h = self._bridge._viewport_h
        if screenshot:
            self._mirror.set_screenshot(screenshot)
        self._mirror.set_elements(elements)
        self.window.title = f"Trome - {title}"
        if not self._url_input._focused:
            self._url_input.text = url
        # Only update status with URL if not currently showing hover info
        if not self._hover_url:
            self._status.text = f" {url}"
        self.app._needs_repaint = True

    # --- Navigation (queue commands for refresh thread) ---

    def _on_url_submit(self, text: str) -> None:
        """Navigate to URL when user presses Enter in URL bar."""
        url = text.strip()
        if not url:
            return
        if not url.startswith(("http://", "https://", "file://")):
            url = "https://" + url
        self._status.text = f" Navigating to {url}..."
        self.app._needs_repaint = True
        self._enqueue_cmd("navigate", url)

    def _go_back(self) -> None:
        self._status.text = " Going back..."
        self._enqueue_cmd("back")

    def _go_forward(self) -> None:
        self._status.text = " Going forward..."
        self._enqueue_cmd("forward")

    def _reload(self) -> None:
        self._status.text = " Reloading..."
        self._enqueue_cmd("reload")

    def _go_home(self) -> None:
        """Clear URL and navigate to about:blank — fresh start."""
        self._url_input.text = ""
        self._url_input._cursor_pos = 0
        self._status.text = " Click the URL bar above and type an address to browse"
        self.window.title = "Trome"
        self._enqueue_cmd("navigate", "about:blank")
        self.app._needs_repaint = True

    # --- Viewport Resize ---

    def _on_mirror_resized(self, cell_w: int, cell_h: int) -> None:
        """Called when the mirror widget's cell dimensions change.

        Converts terminal cells to approximate pixel dimensions and
        tells Chrome to resize its viewport to match.  This makes the
        screenshot fill the widget and keeps DOM element bboxes aligned.
        """
        # Approximate pixel dimensions: each terminal cell is roughly
        # 8px wide and 16px tall.  Use a minimum of 320x240 so Chrome
        # doesn't get an unusably tiny viewport.
        px_w = max(320, cell_w * 8)
        px_h = max(240, cell_h * 16)
        # Update the mirror widget's coordinate mapping immediately
        self._mirror._viewport_w = px_w
        self._mirror._viewport_h = px_h
        # Invalidate the scaled screenshot cache so it re-renders at new size
        self._mirror._scaled_cache = None
        self._mirror._cache_key = ()
        # Queue the resize command for the background thread
        self._enqueue_cmd("resize", px_w, px_h)

    # --- Mirror Interaction (queue commands for refresh thread) ---

    def _on_mirror_click(self, px: int, py: int) -> None:
        """Handle click on the mirror widget — dispatch to Chrome."""
        elem = self._mirror._find_element_at(px, py)
        if elem and elem.element_type == "link" and elem.url:
            self._status.text = f" Link: {elem.url}"
        elif elem and elem.element_type == "button":
            self._status.text = f" Button: {elem.text}"
        self._enqueue_cmd("click", px, py)
        self.app._needs_repaint = True

    def _on_mirror_scroll(self, dx: int, dy: int) -> None:
        """Handle scroll on the mirror widget — dispatch to Chrome."""
        self._enqueue_cmd("scroll", dx, dy)

    def _on_mirror_key(self, kind: str, value: str) -> None:
        """Handle key press on the mirror widget — dispatch to Chrome."""
        if kind == "char":
            self._enqueue_cmd("type", value)
        else:
            self._enqueue_cmd("press", value)

    def _on_mirror_hover(self, elem: DOMElement | None) -> None:
        """Handle mouse hover over an element — show full text in status bar."""
        if elem is None:
            # Mouse left all elements — restore URL display
            if self._hover_url:
                self._hover_url = ""
                url = self._bridge.get_url()
                self._status.text = f" {url}"
                self.app._needs_repaint = True
            return

        # Build hover text for the status bar
        hover = ""
        if elem.element_type == "link" and elem.url:
            hover = f" Link: {elem.url}"
        elif elem.element_type == "button":
            hover = f" Button: {elem.text}"
        elif elem.element_type == "input":
            hover = f" Input: {elem.text}" if elem.text else " Input field"
        else:
            # Show the full text (original before line-splitting)
            full = elem.full_text or elem.text
            if full:
                hover = f" {full}"

        if hover and hover != self._hover_url:
            self._hover_url = hover
            self._status.text = hover
            self.app._needs_repaint = True

    # --- Screenshot Preview ---

    def _open_screenshot_preview(self) -> None:
        """Save current screenshot to temp file and open an image viewer.

        Uses the same ImageViewerWindow pattern as tui_os.py:914.
        """
        if not self._mirror._screenshot:
            return
        try:
            from runtui.widgets.image import ImageWidget

            path = os.path.join(tempfile.gettempdir(), "trome_screenshot.png")
            self._mirror._screenshot.save(path)

            # If running inside TuiOS, use its ImageViewerWindow
            if hasattr(self.app, '_open_image_viewer'):
                self.app._open_image_viewer(path)
            else:
                # Standalone mode — create a simple image window
                from runtui.widgets.image import ImageWidget
                win = Window(title="Screenshot Preview", width=84, height=34)
                iw = ImageWidget(width=80, height=30)
                iw.load(path)
                win.set_content(iw)
                self.app.add_window(win)
        except Exception:
            pass

    # --- Menu ---

    def get_menu(self) -> MenuBar:
        """Return the Trome-specific menu bar."""
        sys_menu = self.app._system_menu() if hasattr(self.app, '_system_menu') else Menu("App", [
            MenuItem("Quit", shortcut="Ctrl+Q", action=self.app.quit),
        ])

        return MenuBar(menus=[
            sys_menu,
            Menu("Navigation", [
                MenuItem("Back", action=self._go_back),
                MenuItem("Forward", action=self._go_forward),
                MenuItem("Reload", shortcut="F5", action=self._reload),
                MenuItem.separator(),
                MenuItem("Close Window", shortcut="Ctrl+W", action=lambda: self.window._do_close()),
            ]),
            Menu("View", [
                MenuItem("Screenshot Preview", action=self._open_screenshot_preview),
            ]),
        ])

    # --- Cleanup ---

    def _on_close(self) -> None:
        """Clean up when window is closed."""
        self._refresh_active = False
        self._bridge.disconnect()
        if hasattr(self.app, '_trome_windows'):
            if self in self.app._trome_windows:
                self.app._trome_windows.remove(self)


# ---------------------------------------------------------------------------
#  TromeApp — Standalone Application
# ---------------------------------------------------------------------------

class TromeApp(App):
    """Standalone Trome application."""

    def __init__(self, url: str = "") -> None:
        super().__init__(theme="dark")
        self._initial_url = url
        self._trome_windows: list[TromeWindow] = []

    def on_ready(self) -> None:
        self._open_trome(self._initial_url)
        self.set_interval(0.1, self._tick)

    def _tick(self) -> None:
        """Periodic tick: drain updates from background refresh threads."""
        for tw in self._trome_windows:
            tw.drain_updates()
            if tw._refresh_active:
                self._needs_repaint = True

    def _system_menu(self) -> Menu:
        return Menu("Trome", [
            MenuItem("New Window", shortcut="Ctrl+N", action=lambda: self._open_trome()),
            MenuItem.separator(),
            MenuItem("Quit", shortcut="Ctrl+Q", action=self.quit),
        ])

    def _open_trome(self, url: str = "") -> None:
        tw = TromeWindow(self, url or self._initial_url or "about:blank")
        self._trome_windows.append(tw)
        self.add_window(tw.window)
        tw.window.on(WindowEvent, lambda e: self._on_window_event(e))
        self.set_menu(tw.get_menu())

    def _on_window_event(self, event: WindowEvent) -> None:
        if event.action == WindowAction.ACTIVATE:
            # Update menu for active window
            for tw in self._trome_windows:
                if tw.window is event.window:
                    self.set_menu(tw.get_menu())
                    break
        elif event.action == WindowAction.CLOSE:
            self.call_later(0.05, self._check_empty)

    def _check_empty(self) -> None:
        if not self._trome_windows:
            self.quit()

    def _handle_key(self, event: KeyEvent) -> None:
        # Ctrl+Q: quit
        if event.key == Keys.CHAR and event.char == "q" and Modifiers.CTRL in event.modifiers:
            self.quit()
            event.mark_handled()
            return

        # Ctrl+N: new window
        if event.key == Keys.CHAR and event.char == "n" and Modifiers.CTRL in event.modifiers:
            self._open_trome()
            event.mark_handled()
            self._needs_repaint = True
            return

        # Ctrl+W: close active window
        if event.key == Keys.CHAR and event.char == "w" and Modifiers.CTRL in event.modifiers:
            if self._window_manager and self._window_manager.active_window:
                self._window_manager.active_window._do_close()
                event.mark_handled()
                self._needs_repaint = True
                return

        # F5: reload
        if event.key == Keys.F5:
            for tw in self._trome_windows:
                if tw.window is (self._window_manager.active_window if self._window_manager else None):
                    tw._reload()
                    event.mark_handled()
                    return

        super()._handle_key(event)

    def _shutdown(self) -> None:
        """Clean up all connections on exit."""
        for tw in self._trome_windows:
            try:
                tw._refresh_active = False
                tw._bridge.disconnect()
            except Exception:
                pass
        super()._shutdown()


# ---------------------------------------------------------------------------
#  Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else ""
    app = TromeApp(url=url)
    app.run()

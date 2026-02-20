"""Image widget -- renders images using Unicode half-block characters.

Uses the lower-half-block character (▄) where the foreground color is the
bottom pixel and the background color is the top pixel.  This achieves
2 vertical pixels per character cell with true-color rendering.

Requires Pillow (PIL) for image loading and scaling.
"""

from __future__ import annotations

from ..core.event import KeyEvent, MouseEvent
from ..core.keys import Keys, Modifiers, MouseAction as MA, MouseButton
from ..core.types import Attrs, Color, Rect, Size
from ..rendering.painter import Painter
from .base import Widget

try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ImageWidget(Widget):
    """Renders an image using half-block Unicode characters.

    Each character cell displays 2 vertical pixels using '▄' (lower half block):
      - background color = top pixel
      - foreground color  = bottom pixel

    Row 0 is a toolbar showing: original size, zoom %, and clickable buttons.
    Rows 1..h are the image canvas.
    """

    MIN_ZOOM = 0.05
    MAX_ZOOM = 16.0

    def __init__(
        self,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 60,
        height: int = 30,
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        self._image: "Image.Image | None" = None
        self._filepath: str = ""
        self._zoom: float = 1.0
        self._offset_x: int = 0  # pan offset in image-pixels
        self._offset_y: int = 0
        self._img_width: int = 0
        self._img_height: int = 0
        self._scaled_cache: "Image.Image | None" = None
        self._cache_key: tuple = ()
        self.can_focus = True

        self.on(KeyEvent, self._handle_key)
        self.on(MouseEvent, self._handle_mouse)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, filepath: str) -> bool:
        """Load an image file. Returns True on success."""
        if not HAS_PIL:
            return False
        try:
            img = Image.open(filepath)
            try:
                img = ImageOps.exif_transpose(img)
            except:
                pass
            img = img.convert("RGB")
            self._image = img
            self._filepath = filepath
            self._img_width = img.width
            self._img_height = img.height
            self._zoom = 1.0
            self._offset_x = 0
            self._offset_y = 0
            self._scaled_cache = None
            self._fit_to_view()
            self.invalidate()
            return True
        except Exception:
            self._image = None
            return False

    # ------------------------------------------------------------------
    # Zoom helpers
    # ------------------------------------------------------------------

    def _canvas_height(self) -> int:
        """Image area height (total height minus 1 toolbar row)."""
        sr = self._screen_rect
        h = sr.height if sr.height > 0 else self.height
        return max(1, h - 1)

    def _canvas_width(self) -> int:
        sr = self._screen_rect
        return sr.width if sr.width > 0 else self.width

    def _fit_to_view(self) -> None:
        """Calculate zoom so the whole image fits in the canvas."""
        if not self._image:
            return
        cw = self._canvas_width()
        ch = self._canvas_height() * 2  # 2 pixels per row

        if self._img_width == 0 or self._img_height == 0:
            return

        zoom_w = cw / self._img_width
        zoom_h = ch / self._img_height
        self._zoom = min(zoom_w, zoom_h)
        self._offset_x = 0
        self._offset_y = 0
        self._scaled_cache = None

    def _zoom_in(self) -> None:
        self._zoom = min(self.MAX_ZOOM, self._zoom * 1.25)
        self._scaled_cache = None
        self.invalidate()

    def _zoom_out(self) -> None:
        self._zoom = max(self.MIN_ZOOM, self._zoom / 1.25)
        self._scaled_cache = None
        self.invalidate()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _get_scaled_image(self, view_w: int, view_h_pixels: int) -> "Image.Image | None":
        """Scale the image and center it on a black canvas, cached."""
        if not self._image:
            return None

        scaled_w = max(1, int(self._img_width * self._zoom))
        scaled_h = max(1, int(self._img_height * self._zoom))

        key = (scaled_w, scaled_h, self._offset_x, self._offset_y, view_w, view_h_pixels)
        if self._cache_key == key and self._scaled_cache is not None:
            return self._scaled_cache

        resample = Image.NEAREST if self._zoom > 2.0 else Image.LANCZOS
        scaled = self._image.resize((scaled_w, scaled_h), resample)

        canvas = Image.new("RGB", (view_w, view_h_pixels), (0, 0, 0))

        paste_x = (view_w - scaled_w) // 2 - self._offset_x
        paste_y = (view_h_pixels - scaled_h) // 2 - self._offset_y

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

        black = Color.from_rgb(0, 0, 0)

        # --- Row 0: Toolbar ---
        self._paint_toolbar(painter, lx, ly, w)

        # --- Rows 1..h-1: Image canvas ---
        canvas_h = max(1, h - 1)
        canvas_y = ly + 1

        painter.fill_rect(lx, canvas_y, w, canvas_h, bg=black)

        if not self._image or not HAS_PIL:
            fg = Color.from_rgb(128, 128, 128)
            msg = "No image loaded" if not self._image else "PIL not available"
            painter.put_str(lx + w // 2 - len(msg) // 2, canvas_y + canvas_h // 2, msg, fg=fg, bg=black)
            return

        view_h_pixels = canvas_h * 2
        canvas_img = self._get_scaled_image(w, view_h_pixels)
        if not canvas_img:
            return

        pixels = canvas_img.load()

        for row in range(canvas_h):
            top_py = row * 2
            bot_py = row * 2 + 1

            for col in range(w):
                tr, tg, tb = pixels[col, top_py]
                if bot_py < view_h_pixels:
                    br, bg_r, bb = pixels[col, bot_py]
                else:
                    br, bg_r, bb = 0, 0, 0

                # ▄ = lower half block: fg = bottom pixel, bg = top pixel
                fg = Color.from_rgb(br, bg_r, bb)
                bg = Color.from_rgb(tr, tg, tb)

                painter.put_char(lx + col, canvas_y + row, "▄", fg, bg)

    def _paint_toolbar(self, painter: Painter, lx: int, ly: int, w: int) -> None:
        """Paint the toolbar row at the top."""
        tb_fg = Color.from_rgb(220, 220, 220)
        tb_bg = Color.from_rgb(50, 50, 50)
        btn_fg = Color.from_rgb(255, 255, 255)
        btn_bg = Color.from_rgb(80, 80, 80)

        # Fill toolbar background
        painter.fill_rect(lx, ly, w, 1, bg=tb_bg)

        # Left: image dimensions
        if self._image:
            dim_text = f" {self._img_width}x{self._img_height}"
        else:
            dim_text = " (no image)"
        painter.put_str(lx, ly, dim_text, fg=tb_fg, bg=tb_bg)

        # Center: zoom percentage
        zoom_pct = int(self._zoom * 100)
        zoom_text = f"{zoom_pct}%"
        zx = lx + w // 2 - len(zoom_text) // 2
        painter.put_str(zx, ly, zoom_text, fg=btn_fg, bg=tb_bg, attrs=Attrs.BOLD)

        # Right: buttons  [-] [Fit] [+]
        btn_str = " [-] [Fit] [+] "
        bx = lx + w - len(btn_str)
        if bx > zx + len(zoom_text):
            painter.put_str(bx, ly, btn_str, fg=btn_fg, bg=btn_bg)
            # Store button hit-ranges as rx-relative (0-based from widget left)
            rel_bx = w - len(btn_str)
            self._btn_minus_rx = (rel_bx + 1, rel_bx + 4)
            self._btn_fit_rx = (rel_bx + 5, rel_bx + 10)
            self._btn_plus_rx = (rel_bx + 11, rel_bx + 14)
        else:
            self._btn_minus_rx = (-1, -1)
            self._btn_fit_rx = (-1, -1)
            self._btn_plus_rx = (-1, -1)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def _handle_key(self, event: KeyEvent) -> None:
        if not self._focused or not self._image:
            return

        if event.key == Keys.CHAR and event.char in ("+", "="):
            self._zoom_in()
            event.mark_handled()
        elif event.key == Keys.CHAR and event.char == "-":
            self._zoom_out()
            event.mark_handled()
        elif event.key == Keys.CHAR and event.char == "0":
            self._fit_to_view()
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.CHAR and event.char == "1":
            self._zoom = 1.0
            self._offset_x = 0
            self._offset_y = 0
            self._scaled_cache = None
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.LEFT:
            self._offset_x -= max(3, int(10 / self._zoom))
            self._scaled_cache = None
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.RIGHT:
            self._offset_x += max(3, int(10 / self._zoom))
            self._scaled_cache = None
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.UP:
            self._offset_y -= max(3, int(10 / self._zoom))
            self._scaled_cache = None
            self.invalidate()
            event.mark_handled()
        elif event.key == Keys.DOWN:
            self._offset_y += max(3, int(10 / self._zoom))
            self._scaled_cache = None
            self.invalidate()
            event.mark_handled()

    def _handle_mouse(self, event: MouseEvent) -> None:
        sr = self._screen_rect
        rx = event.x - sr.x
        ry = event.y - sr.y

        if event.action == MA.PRESS and event.button == MouseButton.LEFT:
            self.focus()
            # Check toolbar button clicks (ry == 0)
            if ry == 0 and hasattr(self, "_btn_minus_rx"):
                if self._btn_minus_rx[0] <= rx < self._btn_minus_rx[1]:
                    self._zoom_out()
                elif self._btn_fit_rx[0] <= rx < self._btn_fit_rx[1]:
                    self._fit_to_view()
                    self.invalidate()
                elif self._btn_plus_rx[0] <= rx < self._btn_plus_rx[1]:
                    self._zoom_in()
            event.mark_handled()
        elif event.button == MouseButton.SCROLL_UP:
            self._zoom_in()
            event.mark_handled()
        elif event.button == MouseButton.SCROLL_DOWN:
            self._zoom_out()
            event.mark_handled()

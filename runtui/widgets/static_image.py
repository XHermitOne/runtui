"""StaticImage widget -- renders a pure image without toolbar or zoom controls.

Uses the lower-half-block character (▄) where the foreground color is the
bottom pixel and the background color is the top pixel.  This achieves
2 vertical pixels per character cell with true-color rendering.

Designed for use in the RAD designer and applications where a simple
image display is needed without interactive zoom/pan controls.

Requires Pillow (PIL) for image loading and scaling.
"""

from __future__ import annotations

from ..core.types import Color, Size
from ..rendering.painter import Painter
from .base import Widget

try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class StaticImage(Widget):
    """Renders an image fit-to-size using half-block Unicode characters.

    Each character cell displays 2 vertical pixels using '▄' (lower half block):
      - background color = top pixel
      - foreground color  = bottom pixel

    The entire widget area is used for the image (no toolbar).
    The image is automatically scaled to fit the widget dimensions.
    """

    def __init__(
        self,
        id: str | None = None,
        x: int = 0,
        y: int = 0,
        width: int = 40,
        height: int = 20,
        filepath: str = "",
    ) -> None:
        super().__init__(id=id, x=x, y=y, width=width, height=height)
        self._image: "Image.Image | None" = None
        self._filepath: str = filepath
        self._img_width: int = 0
        self._img_height: int = 0
        self._scaled_cache: "Image.Image | None" = None
        self._cache_key: tuple = ()
        self.can_focus = False

        if filepath:
            self.load(filepath)

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
            except Exception:
                pass
            img = img.convert("RGB")
            self._image = img
            self._filepath = filepath
            self._img_width = img.width
            self._img_height = img.height
            self._scaled_cache = None
            self.invalidate()
            return True
        except Exception:
            self._image = None
            return False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _get_fitted_image(self, view_w: int, view_h_pixels: int) -> "Image.Image | None":
        """Scale the image to fit the view, centered on a black canvas, cached."""
        if not self._image:
            return None

        key = (self._img_width, self._img_height, view_w, view_h_pixels)
        if self._cache_key == key and self._scaled_cache is not None:
            return self._scaled_cache

        # Calculate zoom to fit
        zoom_w = view_w / self._img_width if self._img_width > 0 else 1.0
        zoom_h = view_h_pixels / self._img_height if self._img_height > 0 else 1.0
        zoom = min(zoom_w, zoom_h)

        scaled_w = max(1, int(self._img_width * zoom))
        scaled_h = max(1, int(self._img_height * zoom))

        resample = Image.NEAREST if zoom > 2.0 else Image.LANCZOS
        scaled = self._image.resize((scaled_w, scaled_h), resample)

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

        black = Color.from_rgb(0, 0, 0)

        # Fill background
        painter.fill_rect(lx, ly, w, h, bg=black)

        if not self._image or not HAS_PIL:
            fg = Color.from_rgb(128, 128, 128)
            msg = "No image" if not self._image else "PIL not available"
            painter.put_str(lx + w // 2 - len(msg) // 2, ly + h // 2, msg, fg=fg, bg=black)
            return

        view_h_pixels = h * 2
        canvas_img = self._get_fitted_image(w, view_h_pixels)
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

"""Theme engine -- manages color palettes, border styles, and glyphs."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.types import BorderChars, BorderStyle, Color


@dataclass
class ThemeDefinition:
    """A complete theme definition."""
    name: str
    colors: dict[str, Color] = field(default_factory=dict)
    borders: dict[str, BorderStyle] = field(default_factory=dict)
    glyphs: dict[str, str] = field(default_factory=dict)


class ThemeEngine:
    """Manages the active theme and provides color/glyph lookups."""

    def __init__(self) -> None:
        self._themes: dict[str, ThemeDefinition] = {}
        self._active: ThemeDefinition | None = None

    def register(self, theme: ThemeDefinition) -> None:
        """Register a theme definition."""
        self._themes[theme.name] = theme

    def set_theme(self, name: str) -> None:
        """Activate a theme by name."""
        if name in self._themes:
            self._active = self._themes[name]

    @property
    def active_theme(self) -> ThemeDefinition | None:
        return self._active

    @property
    def theme_names(self) -> list[str]:
        return list(self._themes.keys())

    def get_color(self, slot: str, fallback: Color = Color.DEFAULT) -> Color:
        """Look up a named color slot in the active theme."""
        if self._active and slot in self._active.colors:
            return self._active.colors[slot]
        # Try hierarchical fallback: "button.focused.fg" -> "button.fg" -> "fg"
        parts = slot.split(".")
        while len(parts) > 1:
            parts.pop(-2)  # remove second-to-last
            key = ".".join(parts)
            if self._active and key in self._active.colors:
                return self._active.colors[key]
        return fallback

    def get_border(self, slot: str, fallback: BorderStyle = BorderStyle.SINGLE) -> BorderStyle:
        if self._active and slot in self._active.borders:
            return self._active.borders[slot]
        return fallback

    def get_glyph(self, slot: str, fallback: str = "") -> str:
        if self._active and slot in self._active.glyphs:
            return self._active.glyphs[slot]
        return fallback

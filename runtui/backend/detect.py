"""Auto-detect platform and create appropriate backend."""

from __future__ import annotations

import platform

from .base import Backend


def create_backend() -> Backend:
    """Create the appropriate backend for the current platform."""
    system = platform.system()
    if system in ("Linux", "Darwin", "FreeBSD"):
        from .unix import UnixBackend
        return UnixBackend()
    elif system == "Windows":
        from .windows import WindowsBackend
        return WindowsBackend()
    else:
        # Fallback to Unix-style (most terminals support ANSI)
        from .unix import UnixBackend
        return UnixBackend()

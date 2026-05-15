"""Theme engine and built-in themes."""

from . import black_white
from . import dark
from . import github
from . import gruvbox
from . import high_contrast
from . import legacy_system
from . import light
from . import nord
from . import solarized
from . import turbo_vision
from . import vscode

# Available Themes
AVAILABLE_THEMES = (black_white.NAME, dark.NAME, github.NAME,
                    github.NAME, gruvbox.NAME, high_contrast.NAME,
                    legacy_system.NAME, light.NAME, nord.NAME,
                    solarized.NAME, turbo_vision.NAME, vscode.NAME)
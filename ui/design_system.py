class Colors:
    """TRIZ "Drafting" palette.

    Layered surfaces (BG -> SURFACE cards -> SURFACE_2 insets -> SURFACE_3
    hover) with a cooler, deeper neutral ramp than flat greys, so the accent
    colors carry the emphasis instead of the chrome. Accents are unchanged, so
    existing module code that hardcodes #38BDF8 / #22C55E / #F59E0B / #EF4444
    still lands on-palette.
    """

    BG = "#0A0F1A"
    SURFACE = "#0F1726"
    SURFACE_2 = "#131D31"
    SURFACE_3 = "#1A2740"
    CONSOLE = "#0A101C"

    BORDER = "#1E2A40"
    BORDER_HI = "#2B3B58"

    TEXT = "#E8EDF6"
    SECONDARY = "#9FB0C8"
    MUTED = "#64748B"
    FAINT = "#3E4C63"

    BLUE = "#38BDF8"
    BLUE_HOVER = "#7DD3FC"
    BLUE_DIM = "#0B2E44"

    GREEN = "#22C55E"
    GREEN_SOFT = "#86EFAC"
    YELLOW = "#F59E0B"
    YELLOW_SOFT = "#FCD34D"
    RED = "#EF4444"
    RED_SOFT = "#FCA5A5"
    PURPLE = "#A78BFA"

    INK = "#001018"
    MONO = "'Cascadia Code', 'Consolas', monospace"

    # Blueprint grid dots
    GRID_MINOR = "#141D33"
    GRID_MAJOR = "#1E2B49"


class Fonts:
    FAMILY = "Segoe UI"

    TITLE = "28px"
    HEADER = "20px"
    BODY = "13px"
    SMALL = "11px"


class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 18
    XL = 24
    XXL = 32


class Radius:
    SM = 4
    MD = 6
    LG = 8


class Sizes:
    SIDEBAR_WIDTH = 280
    HEADER_HEIGHT = 64
    MONITOR_WIDTH = 260
    OUTPUT_HEIGHT = 160


class Levels:
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    MODULE = "MODULE"
    JOB = "JOB"


def level_ink(level: str) -> str:
    """Softer text tone for console log lines — the dot carries the signal."""
    level = level.upper()
    return {
        Levels.INFO: "#B9C6DB",
        Levels.SUCCESS: Colors.GREEN_SOFT,
        Levels.WARNING: Colors.YELLOW_SOFT,
        Levels.ERROR: Colors.RED_SOFT,
        Levels.MODULE: "#C4B5FD",
        Levels.JOB: Colors.BLUE_HOVER,
    }.get(level, Colors.SECONDARY)


def level_color(level: str) -> str:
    level = level.upper()

    return {
        Levels.INFO: Colors.BLUE,
        Levels.SUCCESS: Colors.GREEN,
        Levels.WARNING: Colors.YELLOW,
        Levels.ERROR: Colors.RED,
        Levels.MODULE: Colors.PURPLE,
        Levels.JOB: Colors.YELLOW,
    }.get(level, Colors.TEXT)

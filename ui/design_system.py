class Colors:
    BG = "#0B1120"
    SURFACE = "#111827"
    SURFACE_2 = "#1F2937"
    SURFACE_3 = "#273549"

    BORDER = "#374151"

    TEXT = "#F9FAFB"
    MUTED = "#9CA3AF"

    BLUE = "#38BDF8"
    BLUE_HOVER = "#7DD3FC"

    GREEN = "#22C55E"
    YELLOW = "#F59E0B"
    RED = "#EF4444"
    PURPLE = "#A78BFA"


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

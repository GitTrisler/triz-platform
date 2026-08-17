from PySide6.QtWidgets import (
    QFrame, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QSize

try:
    import qtawesome as qta
    HAS_QTAWESOME = True
except ImportError:
    qta = None
    HAS_QTAWESOME = False


from ui.design_system import Colors

BLUE = Colors.BLUE
GREEN = Colors.GREEN
RED = Colors.RED
PURPLE = Colors.PURPLE
ORANGE = Colors.YELLOW
WHITE = Colors.TEXT
MUTED = Colors.MUTED
SECONDARY = Colors.SECONDARY
FAINT = Colors.FAINT
BORDER = Colors.BORDER
BORDER_HI = Colors.BORDER_HI
DARK = Colors.SURFACE_2
INK = Colors.INK
MONO = Colors.MONO


class SectionHeader(QFrame):
    """Drafting-sheet field label: step chip (or icon), tracked caps, hairline.

    Reads as a drawing annotation rather than a web heading — the rule carries
    the eye across the card and the step number stays legible without shouting.
    """

    def __init__(self, title, step=None, icon=None, color=BLUE):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)

        if step is not None:
            badge = QLabel(str(step))
            badge.setAlignment(Qt.AlignCenter)
            badge.setFixedSize(20, 20)
            badge.setStyleSheet(
                f"color: {color}; border: 1px solid {color};"
                "border-radius: 10px; font-size: 10px; font-weight: 800;"
                "background: transparent;"
            )
            layout.addWidget(badge)

        elif icon and HAS_QTAWESOME:
            icon_label = QLabel()
            icon_label.setPixmap(qta.icon(icon, color=color).pixmap(15, 15))
            layout.addWidget(icon_label)

        else:
            tick = QFrame()
            tick.setFixedSize(3, 11)
            tick.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            layout.addWidget(tick)

        self.label = QLabel(str(title).upper())
        self.label.setStyleSheet(
            f"color: {SECONDARY}; font-size: 11px; font-weight: 800;"
            "letter-spacing: 1.8px; background: transparent;"
        )
        layout.addWidget(self.label)

        rule = QFrame()
        rule.setFixedHeight(1)
        rule.setStyleSheet(f"background-color: {BORDER}; border: none;")
        layout.addWidget(rule, stretch=1)

    def setText(self, text):
        self.label.setText(str(text).upper())


class TRIZCard(QFrame):
    """Surface card carrying drawing-sheet registration ticks at its corners."""

    TICK_INSET = 9
    TICK_LEN = 6

    def __init__(self, title=None, step=None, icon=None, color=BLUE):
        super().__init__()
        self.setObjectName("Card")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 16, 20, 18)
        self.layout.setSpacing(12)

        if title:
            self.layout.addWidget(
                SectionHeader(title=title, step=step, icon=icon, color=color)
            )

    def paintEvent(self, event):
        super().paintEvent(event)
        from PySide6.QtGui import QColor, QPainter, QPen

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(QPen(QColor(BORDER_HI), 1))

        w, h = self.width(), self.height()
        inset, length = self.TICK_INSET, self.TICK_LEN

        for x, y, dx, dy in (
            (inset, inset, 1, 1),
            (w - 1 - inset, inset, -1, 1),
            (inset, h - 1 - inset, 1, -1),
            (w - 1 - inset, h - 1 - inset, -1, -1),
        ):
            painter.drawLine(x, y, x + dx * length, y)
            painter.drawLine(x, y, x, y + dy * length)

        painter.end()


class BlueprintFrame(QFrame):
    """Workspace background: faint drafting dot grid painted in code.

    Qt's QSS background-repeat is unreliable for tiling, so the grid is drawn
    directly — minor dots every 28 px with a brighter major dot every fourth.
    """

    PITCH = 28
    MAJOR_EVERY = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Workspace")

    def paintEvent(self, event):
        from PySide6.QtGui import QColor, QPainter

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.BG))

        minor = QColor(Colors.GRID_MINOR)
        major = QColor(Colors.GRID_MAJOR)
        step = self.PITCH

        for iy, y in enumerate(range(step, self.height(), step)):
            for ix, x in enumerate(range(step, self.width(), step)):
                big = (ix % self.MAJOR_EVERY == 0) and (iy % self.MAJOR_EVERY == 0)
                painter.fillRect(x, y, 2, 2, major if big else minor)

        painter.end()
        super().paintEvent(event)


class TRIZButton(QPushButton):
    def __init__(self, text, kind="default", width=92):
        super().__init__(text)

        self.setMinimumWidth(width)
        self.setMinimumHeight(34)

        self.setCursor(Qt.PointingHandCursor)

        base = ("font-weight: 700; font-size: 12.5px; letter-spacing: 0.3px;"
                "border: none; border-radius: 7px; padding: 8px 14px;")

        filled = {
            "success": (GREEN, "#4ADE80", INK, "#14532D"),
            "danger": (RED, "#F87171", "#FFFFFF", "#450A0A"),
            "default": (BLUE, Colors.BLUE_HOVER, INK, Colors.BLUE_DIM),
        }

        if kind == "ghost":
            self.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {SECONDARY};"
                f" border: 1px solid {BORDER}; font-weight: 600; font-size: 12.5px;"
                " border-radius: 7px; padding: 8px 14px; }"
                f"QPushButton:hover {{ border-color: {BLUE}; color: {BLUE}; }}"
                f"QPushButton:disabled {{ color: {FAINT};"
                f" border-color: {BORDER}; }}"
            )
        else:
            fill, hover, ink, disabled = filled.get(kind, filled["default"])
            self.setStyleSheet(
                f"QPushButton {{ background-color: {fill}; color: {ink}; {base} }}"
                f"QPushButton:hover {{ background-color: {hover}; }}"
                f"QPushButton:pressed {{ background-color: {fill}; }}"
                f"QPushButton:disabled {{ background-color: {disabled};"
                f" color: {MUTED}; }}"
            )


class FormField(QFrame):
    def __init__(
        self,
        label,
        placeholder="",
        widget=None,
        browse_text=None,
        browse_callback=None,
        help_text=None,
        browse_width=105,
    ):
        super().__init__()

        self.setMinimumHeight(58)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.input = widget or QLineEdit()
        self.input.setMinimumHeight(36)
        self.input.setMaximumHeight(36)
        self.input.setMinimumWidth(0)
        self.input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if hasattr(self.input, "setPlaceholderText"):
            self.input.setPlaceholderText(placeholder)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.label = QLabel(str(label).upper())
        self.label.setFixedHeight(14)
        self.label.setStyleSheet(
            f"color: {MUTED}; font-size: 10px; font-weight: 800;"
            "letter-spacing: 1.2px; background: transparent;"
        )

        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(10)

        input_row.addWidget(self.input, 1)

        self.browse_btn = None
        if browse_callback:
            self.browse_btn = QPushButton()
            self.browse_btn.setFixedSize(36, 36)
            self.browse_btn.setMinimumSize(36, 36)
            self.browse_btn.setMaximumSize(36, 36)
            self.browse_btn.setToolTip(browse_text or "Browse")
            self.browse_btn.setCursor(Qt.PointingHandCursor)
            self.browse_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            self.browse_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {DARK};
                    color: {SECONDARY};
                    border: 1px solid {BORDER};
                    border-radius: 7px;
                    padding: 0px;
                    min-width: 36px;
                    max-width: 36px;
                    min-height: 36px;
                    max-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.SURFACE_3};
                    border-color: {BLUE};
                }}
                QPushButton:pressed {{
                    background-color: #0284C7;
                }}
                """
            )

            if HAS_QTAWESOME:
                self.browse_btn.setIcon(qta.icon("fa5s.folder-open", color=SECONDARY))
                self.browse_btn.setIconSize(QSize(18, 18))
            else:
                self.browse_btn.setText("📁")

            self.browse_btn.clicked.connect(browse_callback)
            input_row.addWidget(self.browse_btn, 0)

        input_row.setStretch(0, 1)
        if browse_callback:
            input_row.setStretch(1, 0)

        layout.addWidget(self.label)
        layout.addLayout(input_row)

        self.help_label = None
        if help_text:
            self.help_label = QLabel(help_text)
            self.help_label.setObjectName("Muted")
            self.help_label.setWordWrap(True)
            self.help_label.setStyleSheet("font-size: 11px;")
            layout.addWidget(self.help_label)

    def text(self):
        if hasattr(self.input, "text"):
            return self.input.text()
        return ""

    def set_text(self, value):
        if hasattr(self.input, "setText"):
            self.input.setText(value or "")

    def widget(self):
        return self.input


class MetricTile(QFrame):
    """Metric readout.

    Default (compact=False) keeps the original stacked layout so existing
    modules are untouched. compact=True lays the badge beside the text, which
    roughly halves the tile height — use it wherever several tiles share a
    card and the numbers are short.
    """

    def __init__(self, label, value="0", icon=None, color=BLUE, width=124,
                 compact=False):
        super().__init__()
        self.setObjectName("MetricCard")
        self.compact = compact
        self.setMinimumWidth(126 if compact else width)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        badge_size = 26 if compact else 36
        self.icon_badge = QLabel()
        self.icon_badge.setAlignment(Qt.AlignCenter)
        self.icon_badge.setFixedSize(badge_size, badge_size)
        self.icon_badge.setStyleSheet(
            f"background-color: {color}; border-radius: {badge_size // 2}px;"
        )

        if icon and HAS_QTAWESOME:
            self.icon_badge.setPixmap(
                qta.icon(icon, color=INK).pixmap(13 if compact else 17,
                                                 13 if compact else 17))
        else:
            self.icon_badge.setText("•")
            self.icon_badge.setStyleSheet(
                f"background-color: {color}; color: {INK}; "
                f"border-radius: {badge_size // 2}px; font-weight: 900;"
            )

        self.label = QLabel(label)
        self.label.setWordWrap(not compact)
        self.label.setStyleSheet(
            f"color: {MUTED}; font-size: 9px; font-weight: 800;"
            "letter-spacing: 1.3px; background: transparent;"
        )

        self.value_label = QLabel()
        self.value_label.setWordWrap(False)

        if compact:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(12, 9, 12, 9)
            layout.setSpacing(10)

            self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            text_col = QVBoxLayout()
            text_col.setContentsMargins(0, 0, 0, 0)
            text_col.setSpacing(0)
            text_col.addWidget(self.label)
            text_col.addWidget(self.value_label)

            layout.addWidget(self.icon_badge, alignment=Qt.AlignVCenter)
            layout.addLayout(text_col, stretch=1)
        else:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(6)
            layout.setAlignment(Qt.AlignCenter)

            self.label.setAlignment(Qt.AlignCenter)
            self.value_label.setAlignment(Qt.AlignCenter)
            self.value_label.setMinimumWidth(96)
            self.value_label.setMinimumHeight(34)
            self.value_label.setSizePolicy(QSizePolicy.Expanding,
                                           QSizePolicy.Preferred)

            layout.addWidget(self.icon_badge, alignment=Qt.AlignCenter)
            layout.addWidget(self.label)
            layout.addWidget(self.value_label)

        self.set_value(value)

    def set_value(self, value):
        text = str(value)
        self.value_label.setText(text)
        numeric = text.replace(".", "", 1).isdigit()

        if self.compact:
            size = "21px" if numeric else "13px"
        else:
            size = "28px" if numeric else "16px"

        self.value_label.setStyleSheet(
            f"color: {WHITE}; font-size: {size}; font-weight: 600;"
            "background: transparent;"
        )


TRIZSectionHeader = SectionHeader
TRIZMetricCard = MetricTile


class TRIZButtonRow(QHBoxLayout):
    def __init__(self, spacing=8):
        super().__init__()
        self.setSpacing(spacing)

    def add_stretch_end(self):
        self.addStretch()
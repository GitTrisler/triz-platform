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


BLUE = "#38BDF8"
GREEN = "#22C55E"
RED = "#EF4444"
PURPLE = "#A78BFA"
ORANGE = "#F59E0B"
WHITE = "#F9FAFB"
MUTED = "#9CA3AF"
BORDER = "#374151"
DARK = "#1F2937"
INK = "#001018"


class SectionHeader(QFrame):
    def __init__(self, title, step=None, icon=None, color=BLUE):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        if step is not None:
            badge = QLabel(str(step))
            badge.setAlignment(Qt.AlignCenter)
            badge.setFixedSize(28, 28)
            badge.setStyleSheet(
                f"background-color: {color}; color: {INK}; "
                "border-radius: 14px; font-weight: 900;"
            )
            layout.addWidget(badge)

        elif icon and HAS_QTAWESOME:
            icon_label = QLabel()
            icon_label.setPixmap(qta.icon(icon, color=color).pixmap(18, 18))
            layout.addWidget(icon_label)

        label = QLabel(title)
        label.setStyleSheet(
            f"font-size: 16px; font-weight: 900; color: {color};"
        )

        layout.addWidget(label)
        layout.addStretch()


class TRIZCard(QFrame):
    def __init__(self, title=None, step=None, icon=None, color=BLUE):
        super().__init__()
        self.setObjectName("Card")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(22, 18, 22, 18)
        self.layout.setSpacing(12)

        if title:
            self.layout.addWidget(
                SectionHeader(title=title, step=step, icon=icon, color=color)
            )


class TRIZButton(QPushButton):
    def __init__(self, text, kind="default", width=92):
        super().__init__(text)

        self.setMinimumWidth(width)
        self.setMinimumHeight(34)

        base = "font-weight: 900; border-radius: 5px; padding: 8px 12px;"

        if kind == "success":
            self.setStyleSheet(f"background-color: {GREEN}; color: {INK}; {base}")
        elif kind == "danger":
            self.setStyleSheet(f"background-color: {RED}; color: #FFFFFF; {base}")
        elif kind == "ghost":
            self.setStyleSheet(
                f"background-color: {DARK}; color: {WHITE}; "
                f"border: 1px solid {BORDER}; {base}"
            )
        else:
            self.setStyleSheet(f"background-color: {BLUE}; color: {INK}; {base}")


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

        self.label = QLabel(label)
        self.label.setFixedHeight(16)
        self.label.setStyleSheet(
            f"color: {WHITE}; font-size: 12px; font-weight: 800;"
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
                    background-color: {BLUE};
                    color: {WHITE};
                    border: none;
                    border-radius: 6px;
                    padding: 0px;
                    min-width: 36px;
                    max-width: 36px;
                    min-height: 36px;
                    max-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: #60A5FA;
                }}
                QPushButton:pressed {{
                    background-color: #0284C7;
                }}
                """
            )

            if HAS_QTAWESOME:
                self.browse_btn.setIcon(qta.icon("fa5s.folder-open", color=WHITE))
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
    def __init__(self, label, value="0", icon=None, color=BLUE, width=124):
        super().__init__()
        self.setObjectName("MetricCard")
        self.setMinimumWidth(width)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_badge = QLabel()
        self.icon_badge.setAlignment(Qt.AlignCenter)
        self.icon_badge.setFixedSize(36, 36)
        self.icon_badge.setStyleSheet(
            f"background-color: {color}; border-radius: 18px;"
        )

        if icon and HAS_QTAWESOME:
            self.icon_badge.setPixmap(qta.icon(icon, color=INK).pixmap(17, 17))
        else:
            self.icon_badge.setText("•")
            self.icon_badge.setStyleSheet(
                f"background-color: {color}; color: {INK}; "
                "border-radius: 18px; font-weight: 900;"
            )

        self.label = QLabel(label)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            f"color: {MUTED}; font-size: 10px; font-weight: 800;"
        )

        self.value_label = QLabel()
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setWordWrap(False)
        self.value_label.setMinimumWidth(96)
        self.value_label.setMinimumHeight(34)
        self.value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout.addWidget(self.icon_badge, alignment=Qt.AlignCenter)
        layout.addWidget(self.label)
        layout.addWidget(self.value_label)

        self.set_value(value)

    def set_value(self, value):
        text = str(value)
        self.value_label.setText(text)

        if text.replace(".", "", 1).isdigit():
            self.value_label.setStyleSheet(
                f"color: {WHITE}; font-size: 28px; font-weight: 900;"
            )
        else:
            self.value_label.setStyleSheet(
                f"color: {WHITE}; font-size: 16px; font-weight: 900;"
            )


TRIZSectionHeader = SectionHeader
TRIZMetricCard = MetricTile


class TRIZButtonRow(QHBoxLayout):
    def __init__(self, spacing=8):
        super().__init__()
        self.setSpacing(spacing)

    def add_stretch_end(self):
        self.addStretch()
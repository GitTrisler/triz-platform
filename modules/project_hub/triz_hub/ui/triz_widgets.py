"""
TRIZ platform widget vocabulary — same public API as ui/triz_widgets.py in the
main TRIZ Platform (TRIZCard with .layout, TRIZSectionHeader, TRIZButton
kinds, TRIZMetricCard.set_value, TRIZButtonRow, triz_page_header, input_row),
so Hub pages lift into the platform shell unchanged.

Drafting-system upgrades over the platform originals, all behind the same
call surface:
  · TRIZCard paints drawing-sheet registration ticks in its corners
  · TRIZSectionHeader is a micro-tracked field label with an accent tick and
    a hairline rule (replaces the big bold cyan text)
  · TRIZMetricCard gets a colored under-bar and a 600-weight display value
  · TRIZButton kinds gain hover/pressed/disabled states
"""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout)

try:
    import qtawesome as qta
except ImportError:
    qta = None

from .theme import MONO, PALETTE

ACCENT = PALETTE["accent"]
SUCCESS = PALETTE["success"]
DANGER = PALETTE["error"]


class TRIZCard(QFrame):
    """Surface card with drawing-sheet registration ticks in the corners."""

    TICK_INSET = 9
    TICK_LEN = 6

    def __init__(self, title=None):
        super().__init__()
        self.setObjectName("Card")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 16, 20, 18)
        self.layout.setSpacing(12)
        if title:
            self.layout.addWidget(TRIZSectionHeader(title))

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setPen(QPen(QColor(PALETTE["border_hi"]), 1))
        w, h = self.width(), self.height()
        i, L = self.TICK_INSET, self.TICK_LEN
        for x, y, dx, dy in ((i, i, 1, 1), (w - 1 - i, i, -1, 1),
                             (i, h - 1 - i, 1, -1), (w - 1 - i, h - 1 - i, -1, -1)):
            p.drawLine(x, y, x + dx * L, y)
            p.drawLine(x, y, x, y + dy * L)
        p.end()


class TRIZSectionHeader(QFrame):
    """Field-label style section header: accent tick · tracked caps · hairline."""

    def __init__(self, text):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(9)
        tick = QFrame()
        tick.setFixedSize(3, 11)
        tick.setStyleSheet(f"background: {PALETTE['accent']}; border-radius: 1px;")
        self._label = QLabel(str(text).upper())
        self._label.setStyleSheet(
            f"color: {PALETTE['secondary']}; font-size: 11px; font-weight: 800;"
            "letter-spacing: 1.8px; background: transparent;")
        rule = QFrame()
        rule.setFixedHeight(1)
        rule.setStyleSheet(f"background: {PALETTE['border']}; border: none;")
        row.addWidget(tick)
        row.addWidget(self._label)
        row.addWidget(rule, stretch=1)

    def setText(self, text):
        self._label.setText(str(text).upper())

    def text(self):
        return self._label.text()


class TRIZButton(QPushButton):
    """kinds: default / primary / success / danger / ghost (+ optional qta icon)."""

    _FILLED = {
        "primary": (PALETTE["accent"], PALETTE["accent_hi"], "#001018", "#0E3A52"),
        "success": (PALETTE["success"], "#4ADE80", "#001018", "#14532D"),
        "danger": (PALETTE["error"], "#F87171", "#FFFFFF", "#450A0A"),
    }

    def __init__(self, text, kind="default", icon=None):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        if kind in self._FILLED:
            base, hover, ink, disabled = self._FILLED[kind]
            self.setStyleSheet(
                f"QPushButton {{ background: {base}; color: {ink};"
                " font-weight: 700; font-size: 12.5px; letter-spacing: 0.3px;"
                " border: none; border-radius: 7px; padding: 8px 18px; }"
                f"QPushButton:hover {{ background: {hover}; }}"
                f"QPushButton:pressed {{ background: {base}; }}"
                f"QPushButton:disabled {{ background: {disabled};"
                f" color: {PALETTE['muted']}; }}")
            if icon and qta:
                self.setIcon(qta.icon(icon, color=ink))
        else:
            if kind == "ghost":
                self.setObjectName("GhostButton")
            if icon and qta:
                self.setIcon(qta.icon(icon, color=PALETTE["secondary"]))


class TRIZMetricCard(QFrame):
    def __init__(self, label, value="0", color=None):
        super().__init__()
        self.setObjectName("MetricCard")
        self._color = color or PALETTE["text"]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 12)
        layout.setSpacing(4)
        top = QLabel(str(label).upper())
        top.setStyleSheet(
            f"color: {PALETTE['muted']}; font-size: 9px; font-weight: 800;"
            "letter-spacing: 1.4px; background: transparent;")
        self.value_label = QLabel(str(value))
        self._bar = QFrame()
        self._bar.setFixedSize(26, 2)
        self._apply()
        layout.addWidget(top)
        layout.addWidget(self.value_label)
        layout.addWidget(self._bar)

    def _apply(self):
        self.value_label.setStyleSheet(
            f"color: {self._color}; font-size: 24px; font-weight: 600;"
            "background: transparent;")
        bar = self._color if self._color != PALETTE["text"] else PALETTE["border_hi"]
        self._bar.setStyleSheet(f"background: {bar}; border-radius: 1px;")

    def set_value(self, value, color=None):
        if color:
            self._color = color
            self._apply()
        old_text = self.value_label.text().replace(",", "")
        new_text = str(value)
        if (old_text.isdigit() and new_text.isdigit()
                and old_text != new_text):
            self._animate_count(int(old_text), int(new_text))
        else:
            self.value_label.setText(new_text)

    def _animate_count(self, start: int, end: int):
        if getattr(self, "_anim", None):
            self._anim.stop()
        anim = QVariantAnimation(self)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setDuration(380)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.valueChanged.connect(
            lambda v: self.value_label.setText(str(int(v))))
        anim.finished.connect(lambda: self.value_label.setText(str(end)))
        anim.start()
        self._anim = anim


class TRIZButtonRow(QHBoxLayout):
    def __init__(self):
        super().__init__()
        self.setSpacing(8)

    def add_stretch_end(self):
        self.addStretch()


def triz_page_header(title_text, subtitle_text):
    """The platform's standard page opener: bold title + muted subtitle."""
    title = QLabel(title_text)
    title.setObjectName("Title")
    subtitle = QLabel(subtitle_text)
    subtitle.setObjectName("Subtitle")
    return title, subtitle


def input_row(label_text, input_widget, browse_callback=None, browse_text="Browse"):
    """Label + field (+ optional browse) row, drafting field-label style."""
    row = QHBoxLayout()
    row.setSpacing(12)
    label = QLabel(str(label_text).upper())
    label.setFixedWidth(120)
    label.setStyleSheet(
        f"color: {PALETTE['muted']}; font-size: 10px; font-weight: 800;"
        "letter-spacing: 1.2px; background: transparent;")
    input_widget.setMinimumHeight(36)
    row.addWidget(label)
    row.addWidget(input_widget)
    if browse_callback:
        btn = QPushButton(browse_text)
        if qta:
            btn.setIcon(qta.icon("fa5s.folder-open", color=PALETTE["secondary"]))
        btn.setFixedWidth(105)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(browse_callback)
        row.addWidget(btn)
    return row

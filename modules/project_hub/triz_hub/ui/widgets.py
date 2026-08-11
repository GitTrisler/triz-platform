"""TRIZ Project Hub — shared UI primitives."""

from __future__ import annotations

import html
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout,
                               QPlainTextEdit, QPushButton, QTableWidget,
                               QVBoxLayout, QAbstractItemView, QHeaderView)

from .theme import MONO, PALETTE, SEVERITY_COLORS, SOFT_SEVERITY, TYPE_COLORS


class SegmentBar(QFrame):
    """Slim stacked composition bar + dot legend. set_data([(label, count,
    color), ...]) — the dashboard uses it for documents-by-class and
    objects-by-type."""

    BAR_H = 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments: list[tuple[str, int, str]] = []
        self._legend = QVBoxLayout(self)
        self._legend.setContentsMargins(0, self.BAR_H + 8, 0, 0)
        self._legend.setSpacing(3)
        self.setVisible(False)

    def set_data(self, segments):
        self._segments = [s for s in segments if s[1] > 0]
        while self._legend.count():
            item = self._legend.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                sub = item.layout()
                while sub.count():
                    w = sub.takeAt(0)
                    if w.widget():
                        w.widget().setParent(None)
        for i in range(0, len(self._segments), 2):
            row = QHBoxLayout()
            row.setSpacing(6)
            for label, count, color in self._segments[i:i + 2]:
                dot = QLabel("●")
                dot.setStyleSheet(f"color: {color}; font-size: 8px;"
                                  "background: transparent;")
                cap = QLabel(f"{label.replace('_', ' ')}")
                cap.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 10px;"
                                  "background: transparent;")
                num = QLabel(str(count))
                num.setStyleSheet(f"color: {PALETTE['secondary']};"
                                  "font-size: 10px; font-weight: 700;"
                                  "background: transparent;")
                row.addWidget(dot)
                row.addWidget(cap)
                row.addWidget(num)
                row.addSpacing(6)
            row.addStretch()
            self._legend.addLayout(row)
        self.setVisible(bool(self._segments))
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._segments:
            return
        from PySide6.QtGui import QColor, QPainter, QPainterPath
        total = sum(c for _, c, _ in self._segments) or 1
        w, h = self.width(), self.BAR_H
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        clip = QPainterPath()
        clip.addRoundedRect(0, 0, w, h, 3, 3)
        p.setClipPath(clip)
        x = 0.0
        for _, count, color in self._segments:
            seg = w * count / total
            p.fillRect(int(x), 0, int(seg + 1), h, QColor(color))
            x += seg
        p.end()


class BlueprintFrame(QFrame):
    """Workspace background: drafting-sheet dot grid painted in code (QSS
    background-repeat is unreliable in Qt). Minor dots every 28 px, a slightly
    brighter major dot every 4th — the faint graph-paper feel under the cards."""

    PITCH = 28
    MAJOR_EVERY = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Workspace")

    def paintEvent(self, event):
        from PySide6.QtGui import QColor, QPainter
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(PALETTE["bg"]))
        minor = QColor("#141D33")
        major = QColor("#1E2B49")
        w, h = self.width(), self.height()
        step = self.PITCH
        for iy, y in enumerate(range(step, h, step)):
            for ix, x in enumerate(range(step, w, step)):
                big = (ix % self.MAJOR_EVERY == 0) and (iy % self.MAJOR_EVERY == 0)
                p.fillRect(x, y, 2, 2, major if big else minor)
        p.end()
        super().paintEvent(event)


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")


class Chip(QPushButton):
    def __init__(self, text: str, checked=True, parent=None):
        super().__init__(text, parent)
        self.setObjectName("Chip")
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)


class TagBadge(QLabel):
    """Colored pill for object type / severity / doc class."""

    def __init__(self, text: str, color: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet(
            f"color: {color}; border: 1px solid {color}; border-radius: 8px;"
            "padding: 1px 9px; font-size: 10px; font-weight: 800;"
            "letter-spacing: 0.6px; background: transparent;")


def type_badge(obj_type: str) -> TagBadge:
    return TagBadge(obj_type, TYPE_COLORS.get(obj_type, PALETTE["muted"]))


def severity_badge(sev: str) -> TagBadge:
    return TagBadge(sev, SEVERITY_COLORS.get(sev, PALETTE["muted"]))


class LogView(QPlainTextEdit):
    """Console-grade activity log: faint timestamp, level dot, soft-toned
    message. Same level vocabulary as the Deliverable Publisher OutputPanel
    (info/success/warning/error/job)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Console")
        self.setReadOnly(True)
        self.setMaximumBlockCount(3000)

    def log(self, level: str, msg: str):
        lvl = level.lower()
        dot = SEVERITY_COLORS.get(lvl, PALETTE["muted"])
        txt = SOFT_SEVERITY.get(lvl, PALETTE["secondary"])
        ts = time.strftime("%H:%M:%S")
        self.appendHtml(
            f'<span style="color:{PALETTE["faint"]}">{ts}</span>'
            f'&nbsp;&nbsp;<span style="color:{dot}">●</span>&nbsp; '
            f'<span style="color:{txt}">{html.escape(msg)}</span>')


class ObjectChip(QPushButton):
    """Clickable related-object pill: 'TK-101 ×10'."""

    open_tag = Signal(str)

    def __init__(self, tag: str, obj_type: str, strength: int, parent=None):
        super().__init__(f"{tag}  ×{strength}", parent)
        color = TYPE_COLORS.get(obj_type, PALETTE["muted"])
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{ color: {color}; border: 1px solid {PALETTE['border']};"
            f"border-radius: 8px; padding: 4px 12px; background: {PALETTE['surface2']};"
            f"font-family: {MONO}; font-size: 11.5px; font-weight: 600; }}"
            f"QPushButton:hover {{ border-color: {color};"
            f" background: {PALETTE['surface3']}; }}")
        self.clicked.connect(lambda: self.open_tag.emit(tag))


def make_table(headers: list[str]) -> QTableWidget:
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(34)
    t.setAlternatingRowColors(False)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QAbstractItemView.SingleSelection)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setShowGrid(False)
    t.horizontalHeader().setStretchLastSection(True)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    t.setSortingEnabled(True)
    return t


def stretch_column(table: QTableWidget, col: int):
    """Make one column absorb spare width instead of the last one."""
    h = table.horizontalHeader()
    h.setStretchLastSection(False)
    h.setSectionResizeMode(col, QHeaderView.Stretch)


def colored_item(text: str, color: str | None = None, mono: bool = False):
    from PySide6.QtGui import QColor, QFont
    from PySide6.QtWidgets import QTableWidgetItem
    item = QTableWidgetItem(text)
    if color:
        item.setForeground(QColor(color))
    if mono:
        f = QFont("Cascadia Code")
        f.setStyleHint(QFont.Monospace)
        item.setFont(f)
    return item


class FlowLayout(QLayout):
    """Wrapping layout for chip rows — related objects flow to the next line
    instead of running off-screen on tag-dense sheets."""

    def __init__(self, parent=None, spacing=6):
        super().__init__(parent)
        self._items = []
        self.setSpacing(spacing)
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def clear_widgets(self):
        while self._items:
            it = self._items.pop()
            if it.widget():
                it.widget().setParent(None)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._layout(None, width, dry=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._layout(rect, rect.width())

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        from PySide6.QtCore import QSize
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        return s

    def _layout(self, rect, width, dry=False):
        from PySide6.QtCore import QPoint, QRect
        x = rect.x() if rect else 0
        y = rect.y() if rect else 0
        line_h = 0
        sp = self.spacing()
        for it in self._items:
            hint = it.sizeHint()
            nx = x + hint.width() + sp
            if nx - sp > ((rect.x() if rect else 0) + width) and line_h > 0:
                x = rect.x() if rect else 0
                y += line_h + sp
                nx = x + hint.width() + sp
                line_h = 0
            if not dry:
                it.setGeometry(QRect(QPoint(x, y), hint))
            x = nx
            line_h = max(line_h, hint.height())
        return y + line_h - (rect.y() if rect else 0)


def hbox(*widgets, spacing=8, margins=(0, 0, 0, 0)):
    lay = QHBoxLayout()
    lay.setSpacing(spacing)
    lay.setContentsMargins(*margins)
    for w in widgets:
        if w == "stretch":
            lay.addStretch()
        else:
            lay.addWidget(w)
    return lay

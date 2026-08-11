"""
Platform page scaffold, API-matched to the TRIZ Platform's ModuleWorkspace
(Title/Subtitle, optional WorkflowStepper, left/right columns, progress
widget, scroll container). WorkflowStepper and TRIZProgressWidget are
hub-local stand-ins with the same call surface (set_active_step,
update_progress(current, total, status, current_item), reset), so pages built
here mount in the real platform shell by swapping one import.

Hub additions over the platform original: steps=None hides the stepper,
show_progress=False omits the progress widget, and add_full() inserts a
full-width widget between the columns and the progress area.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QProgressBar,
                               QScrollArea, QVBoxLayout, QWidget)

from .theme import PALETTE


class WorkflowStepper(QFrame):
    """Numbered step rail: done = green check, active = cyan, pending = muted."""

    def __init__(self, steps=None):
        super().__init__()
        self.steps = steps or []
        self._circles: list[QLabel] = []
        self._labels: list[QLabel] = []
        self._lines: list[QFrame] = []
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 4, 2, 4)
        lay.setSpacing(10)
        for i, name in enumerate(self.steps, 1):
            circle = QLabel(str(i))
            circle.setFixedSize(22, 22)
            circle.setAlignment(Qt.AlignCenter)
            label = QLabel(str(name).upper())
            self._circles.append(circle)
            self._labels.append(label)
            lay.addWidget(circle)
            lay.addWidget(label)
            if i < len(self.steps):
                line = QFrame()
                line.setFixedHeight(1)
                line.setMinimumWidth(28)
                self._lines.append(line)
                lay.addWidget(line, stretch=1)
        lay.addStretch()
        if not self.steps:
            self.setVisible(False)
        self.set_active_step(1)

    def set_active_step(self, step_number: int):
        cap = ("font-size: 10.5px; font-weight: 800; letter-spacing: 1.4px;"
               "background: transparent;")
        num = ("border-radius: 11px; font-size: 10px; font-weight: 800;"
               "background: transparent;")
        for i, (circle, label) in enumerate(zip(self._circles, self._labels), 1):
            if i < step_number:      # done
                circle.setText("✓")
                circle.setStyleSheet(
                    f"border: 1px solid {PALETTE['success']};"
                    f"color: {PALETTE['success']}; {num}")
                label.setStyleSheet(f"color: {PALETTE['success_soft']}; {cap}")
            elif i == step_number:   # active
                circle.setText(str(i))
                circle.setStyleSheet(
                    f"background: {PALETTE['accent_dim']};"
                    f"border: 1px solid {PALETTE['accent']};"
                    f"color: {PALETTE['accent_hi']}; {num}")
                label.setStyleSheet(f"color: {PALETTE['text']}; {cap}")
            else:                    # pending
                circle.setText(str(i))
                circle.setStyleSheet(
                    f"border: 1px solid {PALETTE['border_hi']};"
                    f"color: {PALETTE['muted']}; {num}")
                label.setStyleSheet(f"color: {PALETTE['muted']}; {cap}")
        for i, line in enumerate(self._lines, 1):
            done = i < step_number
            line.setStyleSheet(
                f"background: {PALETTE['success'] if done else PALETTE['border_hi']};"
                "border: none;" + ("" if done else ""))


class TRIZProgressWidget(QFrame):
    """Status + bar + current item. Hidden when idle, shown on first update."""

    def __init__(self):
        super().__init__()
        self.setObjectName("ProgressPanel")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 11, 16, 12)
        lay.setSpacing(7)
        top = QHBoxLayout()
        self.status_label = QLabel("IDLE")
        self.status_label.setStyleSheet(
            f"font-size: 10.5px; font-weight: 800; letter-spacing: 1.6px;"
            f"color: {PALETTE['accent']}; background: transparent;")
        self.count_label = QLabel("")
        self.count_label.setStyleSheet(
            f"color: {PALETTE['secondary']}; font-size: 11.5px;"
            f"font-family: 'Cascadia Code', 'Consolas', monospace;"
            "background: transparent;")
        top.addWidget(self.status_label)
        top.addStretch()
        top.addWidget(self.count_label)
        self.bar = QProgressBar()
        self.item_label = QLabel("")
        self.item_label.setObjectName("Muted")
        self.item_label.setStyleSheet(
            f"color: {PALETTE['faint']}; font-size: 10.5px;"
            "font-family: 'Cascadia Code', 'Consolas', monospace;"
            "background: transparent;")
        lay.addLayout(top)
        lay.addWidget(self.bar)
        lay.addWidget(self.item_label)
        self.setVisible(False)

    def update_progress(self, current, total, status="Working", current_item=""):
        self.setVisible(True)
        self.status_label.setText(str(status).upper())
        self.count_label.setText(f"{current} / {total}")
        self.bar.setMaximum(max(int(total), 1))
        self.bar.setValue(int(current))
        fm = self.item_label.fontMetrics()
        self.item_label.setText(
            fm.elidedText(str(current_item), Qt.ElideMiddle, max(self.width() - 60, 200)))

    def reset(self):
        self.setVisible(False)
        self.bar.setValue(0)
        self.item_label.setText("")
        self.count_label.setText("")
        self.status_label.setText("IDLE")


class ModuleWorkspace(QWidget):
    def __init__(self, title, subtitle="", steps=None, left_width=5,
                 right_width=4, scroll=True, show_progress=True):
        super().__init__()
        self.left_width = left_width
        self.right_width = right_width

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 18)
        root.setSpacing(12)

        kicker = QLabel("TRIZ PLATFORM  ▸  PROJECT HUB")
        kicker.setObjectName("Kicker")
        self.title_label = QLabel(title)
        self.title_label.setObjectName("Title")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("Subtitle")
        root.addWidget(kicker)
        root.addWidget(self.title_label)
        root.addWidget(self.subtitle_label)
        root.setSpacing(8)

        self.stepper = WorkflowStepper(steps=steps)
        self.progress_widget = TRIZProgressWidget()

        self.left_column = QVBoxLayout()
        self.left_column.setSpacing(14)
        self.right_column = QVBoxLayout()
        self.right_column.setSpacing(14)

        columns = QHBoxLayout()
        columns.setSpacing(14)
        columns.addLayout(self.left_column, stretch=left_width)
        columns.addLayout(self.right_column, stretch=right_width)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 4, 0)
        self.content_layout.setSpacing(12)
        self.content_layout.addWidget(self.stepper)
        self.content_layout.addLayout(columns)
        if show_progress:
            self.content_layout.addWidget(self.progress_widget)
        self.content_layout.addStretch()

        if scroll:
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setFrameShape(QScrollArea.NoFrame)
            self.scroll_area.setWidget(content)
            self.scroll_area.setStyleSheet(
                "QScrollArea { background: transparent; border: none; }"
                "QScrollArea > QWidget > QWidget { background: transparent; }")
            root.addWidget(self.scroll_area, stretch=1)
        else:
            root.addWidget(content, stretch=1)

    def add_left(self, widget, stretch=0):
        self.left_column.addWidget(widget, stretch=stretch)

    def add_right(self, widget, stretch=0):
        self.right_column.addWidget(widget, stretch=stretch)

    def add_left_stretch(self):
        self.left_column.addStretch()

    def add_right_stretch(self):
        self.right_column.addStretch()

    def add_full(self, widget, stretch=0):
        """Full-width widget between the columns and the progress area."""
        index = self.content_layout.indexOf(self.progress_widget)
        if index >= 0:
            self.content_layout.insertWidget(index, widget, stretch=stretch)
        else:
            self.content_layout.addWidget(widget, stretch=stretch)

    def add_between_columns_and_progress(self, widget):
        self.add_full(widget)

    def set_active_step(self, step_number):
        self.stepper.set_active_step(step_number)

    def update_progress(self, current, total, status="Working", current_item=""):
        self.progress_widget.update_progress(current, total, status, current_item)

    def reset_progress(self):
        self.progress_widget.reset()

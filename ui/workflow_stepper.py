from ui.design_system import Colors
from PySide6.QtWidgets import (QFrame, QLabel, QHBoxLayout, QSizePolicy,
                               QVBoxLayout)
from PySide6.QtCore import Qt


DEFAULT_STEPS = [
    ("Set Up", "Select folders and page setup", "#38BDF8"),
    ("Scan Drawings", "Find DWG files to publish", "#22C55E"),
    ("Publish", "Plot and create PDFs", "#A855F7"),
    ("Complete", "Review results and logs", "#F59E0B"),
]

MUTED = Colors.MUTED
DIM = Colors.BORDER_HI


class WorkflowStepper(QFrame):
    """Drafting-style progress rail.

    Outlined step markers, tracked caps, and hairline connectors that take on
    the step color once complete. Descriptions hide and the connectors absorb
    the slack, so the rail compresses with the window instead of forcing the
    whole workspace wider than its viewport.
    """

    COMPACT_WIDTH = 1000

    def __init__(self, steps=None):
        super().__init__()
        self.setObjectName("Card")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 11, 18, 11)
        layout.setSpacing(12)

        self.steps = []
        self.connectors = []
        step_defs = steps or DEFAULT_STEPS

        for index, (title, subtitle, color) in enumerate(step_defs, start=1):
            if index > 1:
                self.add_connector(layout)
            self.add_step(layout, index, title, subtitle, color)

        self.set_active_step(1)

    def add_step(self, parent, number, title, subtitle, color):
        box = QFrame()
        box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(9)

        badge = QLabel(str(number))
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(22, 22)

        text_box = QVBoxLayout()
        text_box.setSpacing(0)

        title_label = QLabel(str(title).upper())
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(
            f"font-size: 10px; color: {Colors.FAINT}; background: transparent;")
        # Descriptions are helpful, not essential — first thing to go when the
        # workspace is tight.
        subtitle_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

        text_box.addWidget(title_label)
        text_box.addWidget(subtitle_label)

        row.addWidget(badge)
        row.addLayout(text_box)
        parent.addWidget(box)

        self.steps.append((badge, title_label, subtitle_label, color))

    def add_connector(self, parent):
        line = QFrame()
        line.setFixedHeight(1)
        line.setMinimumWidth(16)
        line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        line.setStyleSheet(f"background-color: {DIM}; border: none;")
        parent.addWidget(line, stretch=1)
        self.connectors.append(line)

    def resizeEvent(self, event):
        """Drop the step descriptions on narrow workspaces."""
        super().resizeEvent(event)
        show_subtitles = self.width() >= self.COMPACT_WIDTH
        for _, _, subtitle, _ in self.steps:
            subtitle.setVisible(show_subtitles)

    def set_active_step(self, step_number):
        caps = ("font-size: 11px; font-weight: 800; letter-spacing: 1.3px;"
                "background: transparent;")
        marker = ("border-radius: 11px; font-size: 10px; font-weight: 800;"
                  "background: transparent;")

        for index, (badge, title, subtitle, color) in enumerate(self.steps, start=1):
            if index < step_number:
                badge.setText("✓")
                badge.setStyleSheet(
                    f"border: 1px solid {color}; color: {color}; {marker}")
                title.setStyleSheet(f"color: {color}; {caps}")
            elif index == step_number:
                badge.setText(str(index))
                badge.setStyleSheet(
                    f"background-color: {Colors.BLUE_DIM};"
                    f"border: 1px solid {color}; color: {color}; {marker}")
                title.setStyleSheet(f"color: {Colors.TEXT}; {caps}")
            else:
                badge.setText(str(index))
                badge.setStyleSheet(
                    f"border: 1px solid {DIM}; color: {MUTED}; {marker}")
                title.setStyleSheet(f"color: {MUTED}; {caps}")

        for index, line in enumerate(self.connectors, start=1):
            done = index < step_number
            done_color = self.steps[index - 1][3] if done else DIM
            line.setStyleSheet(f"background-color: {done_color}; border: none;")

from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt


DEFAULT_STEPS = [
    ("Set Up", "Select folders and page setup", "#38BDF8"),
    ("Scan Drawings", "Find DWG files to publish", "#22C55E"),
    ("Publish", "Plot and create PDFs", "#A855F7"),
    ("Complete", "Review results and logs", "#F59E0B"),
]

MUTED = "#9CA3AF"
DIM = "#4B5563"


class WorkflowStepper(QFrame):
    def __init__(self, steps=None):
        super().__init__()
        self.setObjectName("Card")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(18)

        self.steps = []
        step_defs = steps or DEFAULT_STEPS

        for index, (title, subtitle, color) in enumerate(step_defs, start=1):
            if index > 1:
                self.add_arrow(layout)
            self.add_step(layout, index, title, subtitle, color)

        layout.addStretch()

    def add_step(self, parent, number, title, subtitle, color):
        box = QFrame()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        badge = QLabel(str(number))
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(28, 28)

        text_box = QVBoxLayout()
        text_box.setSpacing(1)

        title_label = QLabel(title)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"font-size: 11px; color: {MUTED};")

        text_box.addWidget(title_label)
        text_box.addWidget(subtitle_label)

        row.addWidget(badge)
        row.addLayout(text_box)
        parent.addWidget(box)

        self.steps.append((badge, title_label, subtitle_label, color))

    def add_arrow(self, parent):
        arrow = QLabel("→")
        arrow.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {MUTED};")
        parent.addWidget(arrow)

    def set_active_step(self, step_number):
        for index, (badge, title, subtitle, color) in enumerate(self.steps, start=1):
            if index <= step_number:
                # Active or completed: full color
                badge.setStyleSheet(
                    f"background-color: {color}; color: white; "
                    "border-radius: 14px; font-weight: 900;"
                )
                title.setStyleSheet(
                    f"font-size: 14px; font-weight: 900; color: {color};"
                )
            else:
                # Upcoming: dimmed
                badge.setStyleSheet(
                    f"background-color: {DIM}; color: {MUTED}; "
                    "border-radius: 14px; font-weight: 900;"
                )
                title.setStyleSheet(
                    f"font-size: 14px; font-weight: 900; color: {MUTED};"
                )
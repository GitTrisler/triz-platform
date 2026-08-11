from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QVBoxLayout, QFrame
from PySide6.QtCore import Signal

from ui.triz_widgets import TRIZCard, TRIZButton


class OptionsPanel(TRIZCard):
    save_requested = Signal()
    publish_requested = Signal()
    cancel_requested = Signal()

    def __init__(self):
        super().__init__("Publish Options", step=3, color="#A78BFA")

        self.overwrite_check = QCheckBox("Overwrite existing PDFs")
        self.close_check = QCheckBox("Close drawings after publish")
        self.csv_check = QCheckBox("Write CSV log")

        self.save_btn = TRIZButton("Save", kind="ghost", width=140)
        self.publish_btn = TRIZButton("Publish", kind="success", width=140)
        self.cancel_btn = TRIZButton("Cancel", kind="danger", width=140)
        self.cancel_btn.setEnabled(False)

        self.save_btn.clicked.connect(self.save_requested.emit)
        self.publish_btn.clicked.connect(self.publish_requested.emit)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)

        checks = QVBoxLayout()
        checks.setSpacing(11)
        checks.addWidget(self.overwrite_check)
        checks.addWidget(self.close_check)
        checks.addWidget(self.csv_check)
        checks.addStretch()
        checks.addWidget(self.save_btn)

        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: #374151;")

        actions = QVBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self.publish_btn)
        actions.addWidget(self.cancel_btn)
        actions.addStretch()

        body = QHBoxLayout()
        body.setSpacing(18)
        body.addLayout(checks, stretch=1)
        body.addWidget(divider)
        body.addLayout(actions)

        self.layout.addLayout(body)

    def values(self):
        return {
            "overwrite_pdfs": self.overwrite_check.isChecked(),
            "close_drawings_after_publish": self.close_check.isChecked(),
            "write_csv_log": self.csv_check.isChecked(),
        }

    def set_values(self, values: dict):
        self.overwrite_check.setChecked(bool(values.get("overwrite_pdfs", True)))
        self.close_check.setChecked(bool(values.get("close_drawings_after_publish", True)))
        self.csv_check.setChecked(bool(values.get("write_csv_log", True)))

    def set_publishing(self, active: bool):
        self.publish_btn.setEnabled(not active)
        self.cancel_btn.setEnabled(active)
        self.save_btn.setEnabled(not active)
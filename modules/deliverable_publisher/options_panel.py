from PySide6.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QLabel,
                               QLineEdit, QVBoxLayout, QFrame)
from PySide6.QtCore import Signal

from ui.triz_widgets import TRIZCard, TRIZButton


class OptionsPanel(TRIZCard):
    save_requested = Signal()
    publish_requested = Signal()
    cancel_requested = Signal()

    def __init__(self):
        super().__init__("Publish Options", step=3, color="#A78BFA")

        self.layout_combo = QComboBox()
        self.layout_combo.addItem("Model space only", "model")
        self.layout_combo.addItem("All layouts except Model", "all")
        self.layout_combo.addItem("Layouts containing…", "filter")
        self.layout_combo.setMinimumHeight(34)
        self.layout_combo.currentIndexChanged.connect(self._sync_filter)

        self.layout_filter = QLineEdit()
        self.layout_filter.setPlaceholderText("ISO")
        self.layout_filter.setMinimumHeight(34)
        self.layout_filter.setEnabled(False)

        layout_label = QLabel("LAYOUTS")
        layout_label.setStyleSheet(
            "color: #64748B; font-size: 9px; font-weight: 800;"
            "letter-spacing: 1.2px;")

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
        checks.addWidget(layout_label)
        checks.addWidget(self.layout_combo)
        checks.addWidget(self.layout_filter)
        checks.addWidget(self.overwrite_check)
        checks.addWidget(self.close_check)
        checks.addWidget(self.csv_check)
        checks.addStretch()
        checks.addWidget(self.save_btn)

        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: #1E2A40;")

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

    def _sync_filter(self):
        """The filter box only matters for the 'contains' mode."""
        self.layout_filter.setEnabled(
            self.layout_combo.currentData() == "filter")

    def values(self):
        return {
            "layout_mode": self.layout_combo.currentData(),
            "layout_filter": self.layout_filter.text().strip(),
            "overwrite_pdfs": self.overwrite_check.isChecked(),
            "close_drawings_after_publish": self.close_check.isChecked(),
            "write_csv_log": self.csv_check.isChecked(),
        }

    def set_values(self, values: dict):
        mode = values.get("layout_mode", "model")
        index = self.layout_combo.findData(mode)
        if index >= 0:
            self.layout_combo.setCurrentIndex(index)
        self.layout_filter.setText(values.get("layout_filter", "ISO"))
        self._sync_filter()
        self.overwrite_check.setChecked(bool(values.get("overwrite_pdfs", True)))
        self.close_check.setChecked(bool(values.get("close_drawings_after_publish", True)))
        self.csv_check.setChecked(bool(values.get("write_csv_log", True)))

    def set_publishing(self, active: bool):
        self.publish_btn.setEnabled(not active)
        self.cancel_btn.setEnabled(active)
        self.save_btn.setEnabled(not active)
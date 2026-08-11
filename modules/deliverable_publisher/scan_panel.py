from PySide6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Signal

from ui.triz_widgets import TRIZCard, TRIZButton


class ScanPanel(TRIZCard):
    scan_requested = Signal()
    clear_requested = Signal()

    def __init__(self):
        super().__init__("Scan Drawings", step=2, color="#22C55E")

        self.recurse_check = QCheckBox("Include subfolders")
        self.recurse_check.setChecked(True)

        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("font-size: 32px; font-weight: 900; color: #22C55E;")

        self.status_label = QLabel("Ready to scan")
        self.status_label.setObjectName("Muted")

        self.scan_btn = TRIZButton("Scan Now", kind="success", width=140)
        self.clear_btn = TRIZButton("Clear List", kind="ghost", width=140)

        self.scan_btn.clicked.connect(self.scan_requested.emit)
        self.clear_btn.clicked.connect(self.clear_requested.emit)

        top = QHBoxLayout()
        top.addWidget(self.recurse_check)
        top.addStretch()

        count_row = QHBoxLayout()
        count_row.addWidget(self.count_label)
        count_row.addWidget(QLabel("Drawings Found"))
        count_row.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addWidget(self.scan_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()

        self.layout.addLayout(top)
        self.layout.addWidget(self.status_label)
        self.layout.addLayout(count_row)
        self.layout.addLayout(btn_row)

    def set_scanned(self, count: int):
        self.count_label.setText(str(count))
        self.status_label.setText(
            f"Found {count} drawing(s)" if count else "No drawings found"
        )

    def reset(self):
        self.count_label.setText("0")
        self.status_label.setText("Ready to scan")

    def values(self):
        return {
            "recurse": self.recurse_check.isChecked()
        }

    def set_values(self, values: dict):
        self.recurse_check.setChecked(bool(values.get("recurse", True)))

    def set_publishing(self, active: bool):
        self.scan_btn.setEnabled(not active)
        self.clear_btn.setEnabled(not active)
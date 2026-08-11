from PySide6.QtWidgets import QCheckBox, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Signal

from ui.triz_widgets import TRIZCard, TRIZButton


class OptionsPanel(TRIZCard):
    save_requested = Signal()
    run_requested = Signal()
    cancel_requested = Signal()
    reset_requested = Signal()

    def __init__(self):
        super().__init__("Update Options", step=3, color="#A855F7")

        self.dry_run_check = QCheckBox("Dry run")
        self.replace_fields_check = QCheckBox("Replace FIELD values")
        self.write_blank_values_check = QCheckBox("Write blank Excel values")
        self.include_subfolders_check = QCheckBox("Include subfolders")

        self.dry_run_check.setChecked(True)
        self.include_subfolders_check.setChecked(True)

        self.save_btn = TRIZButton("Save Settings", kind="ghost", width=140)
        self.run_btn = TRIZButton("Run Update", kind="success", width=150)
        self.cancel_btn = TRIZButton("Cancel", kind="danger", width=120)
        self.reset_btn = TRIZButton("Reset", kind="ghost", width=120)

        self.cancel_btn.setEnabled(False)

        self.save_btn.clicked.connect(self.save_requested.emit)
        self.run_btn.clicked.connect(self.run_requested.emit)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        self.reset_btn.clicked.connect(self.reset_requested.emit)

        checks = QVBoxLayout()
        checks.setSpacing(10)
        checks.addWidget(self.dry_run_check)
        checks.addWidget(self.replace_fields_check)
        checks.addWidget(self.write_blank_values_check)
        checks.addWidget(self.include_subfolders_check)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.run_btn)
        buttons.addWidget(self.cancel_btn)
        buttons.addWidget(self.reset_btn)
        buttons.addStretch()

        self.layout.addLayout(checks)
        self.layout.addStretch()
        self.layout.addLayout(buttons)

    def values(self):
        return {
            "dry_run": self.dry_run_check.isChecked(),
            "replace_fields": self.replace_fields_check.isChecked(),
            "write_blank_values": self.write_blank_values_check.isChecked(),
            "include_subfolders": self.include_subfolders_check.isChecked(),
        }

    def set_values(self, values: dict):
        self.dry_run_check.setChecked(bool(values.get("dry_run", True)))
        self.replace_fields_check.setChecked(bool(values.get("replace_fields", False)))
        self.write_blank_values_check.setChecked(bool(values.get("write_blank_values", False)))
        self.include_subfolders_check.setChecked(bool(values.get("include_subfolders", True)))

    def set_running(self, active: bool):
        self.save_btn.setEnabled(not active)
        self.run_btn.setEnabled(not active)
        self.cancel_btn.setEnabled(active)
        self.reset_btn.setEnabled(not active)
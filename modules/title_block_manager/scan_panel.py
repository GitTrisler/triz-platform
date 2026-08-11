from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Signal

from ui.triz_widgets import TRIZCard, TRIZButton


class ScanPanel(TRIZCard):
    extract_requested = Signal()
    clear_requested = Signal()

    def __init__(self):
        super().__init__(
            "Extract Template",
            step=2,
            color="#22C55E",
        )

        self.status = QLabel("Ready to extract title block data.")
        self.status.setObjectName("Muted")

        self.drawings = QLabel("0")
        self.attributes = QLabel("0")
        self.template_rows = QLabel("0")

        for label in (self.drawings, self.attributes, self.template_rows):
            label.setStyleSheet("""
                font-size:24px;
                font-weight:900;
                color:#22C55E;
            """)

        metrics = QHBoxLayout()
        metrics.setSpacing(18)

        metrics.addLayout(self._metric_column("Drawings", self.drawings))
        metrics.addLayout(self._metric_column("Attributes", self.attributes))
        metrics.addLayout(self._metric_column("Excel Rows", self.template_rows))
        metrics.addStretch()

        self.extract_btn = TRIZButton(
            "Generate Excel Template",
            kind="success",
            width=210,
        )

        self.clear_btn = TRIZButton(
            "Reset",
            kind="ghost",
            width=120,
        )

        self.extract_btn.clicked.connect(self.extract_requested.emit)
        self.clear_btn.clicked.connect(self.clear_requested.emit)

        buttons = QHBoxLayout()
        buttons.addWidget(self.extract_btn)
        buttons.addWidget(self.clear_btn)
        buttons.addStretch()

        self.layout.addWidget(self.status)
        self.layout.addSpacing(8)
        self.layout.addLayout(metrics)
        self.layout.addStretch()
        self.layout.addLayout(buttons)

    def _metric_column(self, title, value):
        col = QVBoxLayout()

        caption = QLabel(title)
        caption.setObjectName("Muted")

        col.addWidget(value)
        col.addWidget(caption)

        return col

    def set_results(
        self,
        drawings,
        attributes,
        rows,
        status="Template generated successfully.",
    ):
        self.drawings.setText(str(drawings))
        self.attributes.setText(str(attributes))
        self.template_rows.setText(str(rows))
        self.status.setText(status)

    def reset(self):
        self.drawings.setText("0")
        self.attributes.setText("0")
        self.template_rows.setText("0")
        self.status.setText("Ready to extract title block data.")
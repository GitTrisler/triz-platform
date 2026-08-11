from PySide6.QtWidgets import QHBoxLayout

from ui.triz_widgets import TRIZCard, MetricTile


class SummaryPanel(TRIZCard):
    def __init__(self):
        super().__init__(
            "Summary",
            step=4,
            color="#F59E0B"
        )

        row = QHBoxLayout()
        row.setSpacing(14)

        self.drawings = MetricTile(
            label="Drawings",
            value="0",
            icon="fa5s.file-alt",
            color="#38BDF8",
        )

        self.processed = MetricTile(
            label="Processed",
            value="0",
            icon="fa5s.check-circle",
            color="#22C55E",
        )

        self.pdfs = MetricTile(
            label="PDFs",
            value="0",
            icon="fa5s.file-pdf",
            color="#A78BFA",
        )

        self.failed = MetricTile(
            label="Failed",
            value="0",
            icon="fa5s.exclamation-triangle",
            color="#EF4444",
        )

        self.status = MetricTile(
            label="Status",
            value="Ready",
            icon="fa5s.flag",
            color="#F59E0B",
        )

        row.addWidget(self.drawings)
        row.addWidget(self.processed)
        row.addWidget(self.pdfs)
        row.addWidget(self.failed)
        row.addWidget(self.status)

        self.layout.addLayout(row)

    def reset(self):
        self.set_drawings(0)
        self.set_processed(0)
        self.set_pdfs(0)
        self.set_failed(0)
        self.set_status("Ready")

    def set_drawings(self, value):
        self.drawings.set_value(value)

    def set_processed(self, value):
        self.processed.set_value(value)

    def set_pdfs(self, value):
        self.pdfs.set_value(value)

    def set_failed(self, value):
        self.failed.set_value(value)

    def set_status(self, value):
        self.status.set_value(value)

    def apply_result(self, result: dict):
        processed = result.get("processed_dwgs", 0)
        plotted = result.get("layouts_plotted", 0)
        failed = (
            result.get("layouts_failed", 0)
            + result.get("failed_dwgs", 0)
        )

        self.set_processed(processed)
        self.set_pdfs(plotted)
        self.set_failed(failed)
        self.set_status("Complete")
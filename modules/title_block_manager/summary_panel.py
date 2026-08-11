from PySide6.QtWidgets import QGridLayout

from ui.triz_widgets import TRIZCard, MetricTile


class SummaryPanel(TRIZCard):
    def __init__(self):
        super().__init__("Summary", step=4, color="#F59E0B")

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        self.drawings = MetricTile(
            label="Drawings",
            value="0",
            icon="fa5s.file-alt",
            color="#38BDF8",
        )

        self.rows = MetricTile(
            label="Rows",
            value="0",
            icon="fa5s.table",
            color="#A78BFA",
        )

        self.matched = MetricTile(
            label="Matched",
            value="0",
            icon="fa5s.check-circle",
            color="#22C55E",
        )

        self.updated = MetricTile(
            label="Updated",
            value="0",
            icon="fa5s.pen",
            color="#F59E0B",
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

        grid.addWidget(self.drawings, 0, 0)
        grid.addWidget(self.rows, 0, 1)
        grid.addWidget(self.matched, 1, 0)
        grid.addWidget(self.updated, 1, 1)
        grid.addWidget(self.failed, 2, 0)
        grid.addWidget(self.status, 2, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.layout.addLayout(grid)

    def reset(self):
        self.set_drawings(0)
        self.set_rows(0)
        self.set_matched(0)
        self.set_updated(0)
        self.set_failed(0)
        self.set_status("Ready")

    def set_drawings(self, value):
        self.drawings.set_value(value)

    def set_rows(self, value):
        self.rows.set_value(value)

    def set_matched(self, value):
        self.matched.set_value(value)

    def set_updated(self, value):
        self.updated.set_value(value)

    def set_failed(self, value):
        self.failed.set_value(value)

    def set_status(self, value):
        self.status.set_value(value)
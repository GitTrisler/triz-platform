from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from ui.output_panel import OutputPanel


class LogsPage(QWidget):
    def __init__(self, output_panel: OutputPanel):
        super().__init__()

        self.output_panel = output_panel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("Logs")
        title.setObjectName("Title")

        layout.addWidget(title)
        layout.addWidget(self.output_panel)
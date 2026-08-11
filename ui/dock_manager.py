from PySide6.QtWidgets import QWidget, QSplitter, QVBoxLayout
from PySide6.QtCore import Qt

from ui.service_monitor import ServiceMonitor


class DockManager(QWidget):
    def __init__(self, workspace):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.monitor = ServiceMonitor()

        horizontal = QSplitter(Qt.Horizontal)
        horizontal.addWidget(workspace)
        horizontal.addWidget(self.monitor)
        horizontal.setStretchFactor(0, 8)
        horizontal.setStretchFactor(1, 2)
        horizontal.setSizes([950, 260])

        layout.addWidget(horizontal)
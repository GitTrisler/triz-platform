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
        horizontal.setStretchFactor(0, 1)
        horizontal.setStretchFactor(1, 0)
        horizontal.setSizes([1100, 250])
        # The workspace holds the real content; the rail is reference data, so
        # only the workspace grows when the window does.
        horizontal.setCollapsible(0, False)
        horizontal.setChildrenCollapsible(True)
        self.monitor.setMaximumWidth(270)

        layout.addWidget(horizontal)
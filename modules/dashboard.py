import sys

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QPushButton
)
from PySide6.QtCore import Qt


class MetricCard(QFrame):
    def __init__(self, label, value, color="#E8EDF6"):
        super().__init__()
        self.setObjectName("MetricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        top = QLabel(label.upper())
        top.setObjectName("Muted")
        top.setStyleSheet("font-size: 10px; font-weight: 800;")

        bottom = QLabel(value)
        bottom.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {color};")

        layout.addWidget(top)
        layout.addWidget(bottom)


class DashboardCard(QFrame):
    def __init__(self, module, open_callback):
        super().__init__()
        self.setObjectName("Card")

        title = module.get("name", "Unnamed Module")
        description = module.get("description", "No description provided.")
        accent = module.get("accent", "#38BDF8")
        category = module.get("category", "General")
        version = module.get("version", "1.0.0")
        author = module.get("author", "Trisler Automation")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        accent_bar = QFrame()
        accent_bar.setFixedHeight(5)
        accent_bar.setStyleSheet(f"background-color: {accent}; border-radius: 2px;")

        status = QLabel("● INSTALLED")
        status.setStyleSheet("font-size: 10px; font-weight: 900; color: #22C55E;")

        category_label = QLabel(category.upper())
        category_label.setObjectName("Muted")
        category_label.setStyleSheet("font-size: 9px; font-weight: 800;")

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 19px; font-weight: 900;")

        desc_label = QLabel(description)
        desc_label.setObjectName("Muted")
        desc_label.setWordWrap(True)

        meta = QLabel(f"Version {version}  |  {author}")
        meta.setObjectName("Muted")
        meta.setStyleSheet("font-size: 10px;")

        open_btn = QPushButton("Open")
        open_btn.setFixedWidth(100)
        open_btn.clicked.connect(lambda: open_callback(title))

        layout.addWidget(accent_bar)
        layout.addWidget(status)
        layout.addWidget(category_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(meta)
        layout.addWidget(open_btn, alignment=Qt.AlignLeft)


class DashboardPage(QWidget):
    def __init__(self, config, modules=None, open_callback=None):
        super().__init__()

        self.config = config
        self.modules = modules or []
        self.open_callback = open_callback or (lambda name: None)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        title = QLabel("Dashboard")
        title.setObjectName("Title")

        subtitle = QLabel(
            f"Welcome back, {config.get('user', 'Cody')}. "
            "Your engineering automation workspace is ready."
        )
        subtitle.setObjectName("Subtitle")

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        metrics.addWidget(MetricCard("Platform", "Online", "#22C55E"))
        metrics.addWidget(MetricCard("Python", f"{sys.version_info.major}.{sys.version_info.minor}", "#38BDF8"))
        metrics.addWidget(MetricCard("Modules", str(len(self.modules)), "#F59E0B"))
        metrics.addWidget(MetricCard("Status", "Ready", "#22C55E"))

        module_grid = QGridLayout()
        module_grid.setSpacing(14)

        if self.modules:
            for i, module in enumerate(self.modules):
                module_grid.addWidget(
                    DashboardCard(module, self.open_callback),
                    i // 2,
                    i % 2
                )
        else:
            empty = QLabel("No modules discovered yet.")
            empty.setObjectName("Muted")
            module_grid.addWidget(empty, 0, 0)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(metrics)
        layout.addLayout(module_grid)
        layout.addStretch()

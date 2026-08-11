from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel
)
from PySide6.QtCore import Qt


class CommandPalette(QDialog):
    def __init__(self, parent=None, registry=None, open_callback=None):
        super().__init__(parent)

        self.registry = registry
        self.open_callback = open_callback or (lambda name: None)
        self.items = []

        self.setWindowTitle("Command Palette")
        self.setModal(True)
        self.resize(520, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Command Palette")
        title.setStyleSheet("font-size: 18px; font-weight: 900;")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search modules or commands...")
        self.search.textChanged.connect(self.filter_items)
        self.search.returnPressed.connect(self.launch_selected)

        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self.launch_item)

        layout.addWidget(title)
        layout.addWidget(self.search)
        layout.addWidget(self.results)

        self.load_items()

    def load_items(self):
        self.items.clear()

        self.items.append({
            "label": "Dashboard",
            "target": "Dashboard",
            "type": "Page"
        })

        self.items.append({
            "label": "Logs",
            "target": "Logs",
            "type": "Administration"
        })

        self.items.append({
            "label": "Settings",
            "target": "Settings",
            "type": "Administration"
        })

        if self.registry:
            for module in self.registry.all():
                self.items.append({
                    "label": module.name,
                    "target": module.name,
                    "type": module.category
                })

        self.filter_items("")

    def filter_items(self, text):
        query = text.strip().lower()
        self.results.clear()

        for item in self.items:
            haystack = f"{item['label']} {item['type']}".lower()

            if not query or query in haystack:
                row = QListWidgetItem(f"{item['label']}    [{item['type']}]")
                row.setData(Qt.UserRole, item["target"])
                self.results.addItem(row)

        if self.results.count() > 0:
            self.results.setCurrentRow(0)

    def launch_selected(self):
        current = self.results.currentItem()
        if current:
            self.launch_item(current)

    def launch_item(self, item):
        target = item.data(Qt.UserRole)
        self.open_callback(target)
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.search.clear()
        self.search.setFocus()
        self.filter_items("")

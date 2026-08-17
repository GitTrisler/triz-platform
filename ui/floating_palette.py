from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent


class FloatingCommandPalette(QDialog):
    def __init__(self, parent=None, registry=None, open_callback=None):
        super().__init__(parent)

        self.registry = registry
        self.open_callback = open_callback or (lambda name: None)
        self.items = []

        self.setWindowFlags(
            Qt.Dialog |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.resize(600, 460)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        shell = QFrame()
        shell.setObjectName("CommandPaletteShell")
        shell.setStyleSheet("""
            QFrame#CommandPaletteShell {
                background-color: #0F1726;
                border: 1px solid #1E2A40;
                border-radius: 12px;
            }
            QLabel {
                color: #E8EDF6;
                font-family: Segoe UI;
            }
            QLineEdit {
                background-color: #0A0F1A;
                color: #E8EDF6;
                border: 1px solid #1E2A40;
                border-radius: 8px;
                padding: 12px 14px;
                font-size: 14px;
                font-family: Segoe UI;
            }
            QListWidget {
                background-color: #0F1726;
                color: #E8EDF6;
                border: none;
                font-size: 14px;
                font-family: Segoe UI;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #131D31;
                border-left: 4px solid #38BDF8;
            }
        """)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Command Palette")
        title.setStyleSheet("font-size: 20px; font-weight: 900;")

        hint = QLabel("Type a module, page, or command. Use Enter to open, Esc to close.")
        hint.setStyleSheet("color: #64748B; font-size: 12px;")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search modules or commands...")
        self.search.textChanged.connect(self.filter_items)
        self.search.returnPressed.connect(self.launch_selected)

        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self.launch_item)

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.search)
        layout.addWidget(self.results)

        outer.addWidget(shell)

        self.load_items()

    def load_items(self):
        self.items.clear()

        self.items.extend([
            {
                "label": "Dashboard",
                "target": "Dashboard",
                "type": "Page",
                "icon": "🏠"
            },
            {
                "label": "Logs",
                "target": "Logs",
                "type": "Administration",
                "icon": "📋"
            },
            {
                "label": "Settings",
                "target": "Settings",
                "type": "Administration",
                "icon": "⚙"
            },
        ])

        if self.registry:
            for module in self.registry.all():
                icon = self.icon_for_category(module.category)

                self.items.append({
                    "label": module.name,
                    "target": module.name,
                    "type": module.category,
                    "icon": icon
                })

        self.filter_items("")

    def icon_for_category(self, category):
        category = (category or "").lower()

        if "util" in category:
            return "🧰"
        if "drawing" in category:
            return "📐"
        if "plant" in category:
            return "🏭"
        if "pdf" in category:
            return "📄"
        if "admin" in category:
            return "⚙"

        return "🔹"

    def filter_items(self, text):
        query = text.strip().lower()
        self.results.clear()

        for item in self.items:
            haystack = f"{item['label']} {item['type']}".lower()

            if not query or query in haystack:
                row = QListWidgetItem(
                    f"{item['icon']}  {item['label']}\n    {item['type']}"
                )
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

        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + 120
            self.move(x, y)

        self.search.clear()
        self.search.setFocus()
        self.filter_items("")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.reject()
            return

        super().keyPressEvent(event)

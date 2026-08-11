from pathlib import Path

from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QListWidget, QFrame

from ui.triz_widgets import TRIZCard


class DrawingListPanel(TRIZCard):
    def __init__(self):
        super().__init__()

        self.drawings = []

        header = QHBoxLayout()

        self.heading = QLabel("DWG List (0)")
        self.heading.setStyleSheet(
            "font-size: 16px; font-weight: 900; color: #F9FAFB;"
        )

        menu = QLabel("☷")
        menu.setObjectName("Muted")
        menu.setStyleSheet("font-size: 18px;")

        header.addWidget(self.heading)
        header.addStretch()
        header.addWidget(menu)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(190)

        self.empty_label = QLabel("Scan drawings to populate this list.")
        self.empty_label.setObjectName("Muted")

        self.layout.addLayout(header)
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.empty_label)

    def set_drawings(self, drawings):
        self.drawings = [Path(dwg) for dwg in drawings]

        self.list_widget.clear()

        for dwg in self.drawings:
            self.list_widget.addItem(dwg.name)

        self.heading.setText(f"DWG List ({len(self.drawings)})")
        self.empty_label.setVisible(len(self.drawings) == 0)

    def clear(self):
        self.drawings.clear()
        self.list_widget.clear()
        self.heading.setText("DWG List (0)")
        self.empty_label.setVisible(True)

    def count(self):
        return len(self.drawings)

    def selected(self):
        selected = []

        for item in self.list_widget.selectedItems():
            index = self.list_widget.row(item)

            if 0 <= index < len(self.drawings):
                selected.append(self.drawings[index])

        return selected
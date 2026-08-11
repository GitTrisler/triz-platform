from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QLineEdit, QPushButton
from PySide6.QtCore import Qt

from core.settings import save_config
from core.logger import log


class SettingsPage(QWidget):
    def __init__(self, config):
        super().__init__()

        self.config = config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        title = QLabel("Settings")
        title.setObjectName("Title")

        subtitle = QLabel("Shared TRIZ Platform configuration.")
        subtitle.setObjectName("Subtitle")

        card = QFrame()
        card.setObjectName("Card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(10)

        name_label = QLabel("User Name")
        name_label.setObjectName("Muted")

        self.user_entry = QLineEdit()
        self.user_entry.setText(config.get("user", "Cody"))
        self.user_entry.setFixedWidth(280)

        save_btn = QPushButton("Save Settings")
        save_btn.setFixedWidth(140)
        save_btn.clicked.connect(self.save)

        card_layout.addWidget(name_label)
        card_layout.addWidget(self.user_entry)
        card_layout.addSpacing(8)
        card_layout.addWidget(save_btn, alignment=Qt.AlignLeft)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(card)
        layout.addStretch()

    def save(self):
        self.config["user"] = self.user_entry.text().strip() or "Cody"
        save_config(self.config)
        log("Settings saved.")

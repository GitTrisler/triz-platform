from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame


class PlaceholderPage(QWidget):
    def __init__(self, title, category):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        title_label = QLabel(title)
        title_label.setObjectName("Title")

        subtitle = QLabel(category)
        subtitle.setObjectName("Subtitle")

        card = QFrame()
        card.setObjectName("Card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)

        msg = QLabel(f"{title} module placeholder.")
        msg.setStyleSheet("font-size: 19px; font-weight: 800;")

        detail = QLabel("This module is registered in the platform but not migrated yet.")
        detail.setObjectName("Muted")
        detail.setWordWrap(True)

        card_layout.addWidget(msg)
        card_layout.addWidget(detail)

        layout.addWidget(title_label)
        layout.addWidget(subtitle)
        layout.addWidget(card)
        layout.addStretch()

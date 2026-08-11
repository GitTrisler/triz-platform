from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout
)
from PySide6.QtCore import Qt


class Card(QFrame):

    def __init__(
        self,
        title,
        description,
        accent="#38BDF8",
        button_text="Open"
    ):

        super().__init__()

        self.setObjectName("Card")

        layout = QVBoxLayout(self)

        layout.setContentsMargins(18, 18, 18, 18)

        layout.setSpacing(10)

        accent_bar = QFrame()
        accent_bar.setFixedHeight(4)
        accent_bar.setStyleSheet(
            f"""
            background:{accent};
            border-radius:2px;
            """
        )

        title_label = QLabel(title)
        title_label.setStyleSheet(
            """
            font-size:18px;
            font-weight:700;
            """
        )

        desc = QLabel(description)
        desc.setWordWrap(True)
        desc.setObjectName("Muted")

        self.button = QPushButton(button_text)

        layout.addWidget(accent_bar)
        layout.addWidget(title_label)
        layout.addWidget(desc)
        layout.addStretch()
        layout.addWidget(
            self.button,
            alignment=Qt.AlignLeft
        )

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QLineEdit
)


class Header(QFrame):

    def __init__(self, user="User"):

        super().__init__()

        self.setObjectName("Header")
        self.setFixedHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)

        badge = QLabel("TRIZ")
        badge.setObjectName("TRIZBadge")

        title = QLabel("Platform")
        title.setStyleSheet("font-size:20px;font-weight:800;")

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Search modules or commands..."
        )

        self.search.setFixedWidth(380)

        self.notifications = QPushButton("Notifications")
        self.notifications.setObjectName("GhostButton")

        username = QLabel(user)
        username.setObjectName("Muted")

        layout.addWidget(badge)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.search)
        layout.addWidget(self.notifications)
        layout.addWidget(username)

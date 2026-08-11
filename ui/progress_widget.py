from PySide6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar
)


class TRIZProgressWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        header = QHBoxLayout()

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 15px; font-weight: 900; color: #38BDF8;")

        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("Muted")

        header.addWidget(self.status_label)
        header.addStretch()
        header.addWidget(self.percent_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        details = QHBoxLayout()

        self.current_label = QLabel("Current: --")
        self.current_label.setObjectName("Muted")

        self.count_label = QLabel("0 / 0")
        self.count_label.setObjectName("Muted")

        details.addWidget(self.current_label)
        details.addStretch()
        details.addWidget(self.count_label)

        layout.addLayout(header)
        layout.addWidget(self.progress)
        layout.addLayout(details)

    def reset(self):
        self.status_label.setText("Ready")
        self.percent_label.setText("0%")
        self.progress.setValue(0)
        self.current_label.setText("Current: --")
        self.count_label.setText("0 / 0")

    def update_progress(self, current, total, status="Working", current_item=""):
        total = max(total, 1)
        percent = int((current / total) * 100)

        self.status_label.setText(status)
        self.percent_label.setText(f"{percent}%")
        self.progress.setValue(percent)
        self.current_label.setText(f"Current: {current_item or '--'}")
        self.count_label.setText(f"{current} / {total}")

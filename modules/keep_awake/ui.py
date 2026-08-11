import ctypes
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QLineEdit, QCheckBox
)

from core.logger import log
from core.module_sdk import TRIZModule, ModuleInfo
from core.module_settings import ModuleSettings


ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


class KeepAwakePage(QWidget):
    def __init__(self):
        super().__init__()

        self.enabled = False

        self.settings = ModuleSettings(
            "keep_awake",
            defaults={
                "interval_seconds": 30,
                "keep_display_awake": True
            }
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        title = QLabel("Keep Awake")
        title.setObjectName("Title")

        subtitle = QLabel("Windows idle prevention utility.")
        subtitle.setObjectName("Subtitle")

        card = QFrame()
        card.setObjectName("Card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(14)

        self.status = QLabel("PAUSED")
        self.status.setStyleSheet(
            "font-size: 26px; font-weight: 900; color: #EF4444;"
        )

        row = QHBoxLayout()

        interval_label = QLabel("Refresh interval:")
        interval_label.setObjectName("Muted")

        self.interval = QLineEdit(
            str(self.settings.get("interval_seconds", 30))
        )
        self.interval.setFixedWidth(80)

        seconds = QLabel("seconds")
        seconds.setObjectName("Muted")

        row.addWidget(interval_label)
        row.addWidget(self.interval)
        row.addWidget(seconds)
        row.addStretch()

        self.display_check = QCheckBox("Keep display awake")
        self.display_check.setChecked(
            bool(self.settings.get("keep_display_awake", True))
        )

        buttons = QHBoxLayout()

        start_btn = QPushButton("Start")
        pause_btn = QPushButton("Pause")
        refresh_btn = QPushButton("Refresh Now")
        save_btn = QPushButton("Save Settings")

        start_btn.clicked.connect(self.start)
        pause_btn.clicked.connect(self.pause)
        refresh_btn.clicked.connect(self.refresh_now)
        save_btn.clicked.connect(self.save_settings)

        buttons.addWidget(start_btn)
        buttons.addWidget(pause_btn)
        buttons.addWidget(refresh_btn)
        buttons.addWidget(save_btn)
        buttons.addStretch()

        self.last_refresh = QLabel("Last refresh: --")
        self.last_refresh.setObjectName("Muted")

        card_layout.addWidget(self.status)
        card_layout.addLayout(row)
        card_layout.addWidget(self.display_check)
        card_layout.addLayout(buttons)
        card_layout.addWidget(self.last_refresh)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(card)
        layout.addStretch()

    def set_keep_awake(self, active: bool):
        if active:
            flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED

            if self.display_check.isChecked():
                flags |= ES_DISPLAY_REQUIRED

            ctypes.windll.kernel32.SetThreadExecutionState(flags)
        else:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

    def save_settings(self):
        try:
            interval = int(self.interval.text().strip())
            if interval < 5:
                interval = 5
        except ValueError:
            interval = 30
            self.interval.setText("30")

        self.settings.update({
            "interval_seconds": interval,
            "keep_display_awake": self.display_check.isChecked()
        })

        log("Keep Awake settings saved.")

    def start(self):
        self.save_settings()
        self.enabled = True
        self.status.setText("ACTIVE")
        self.status.setStyleSheet(
            "font-size: 26px; font-weight: 900; color: #22C55E;"
        )
        self.refresh_now()
        log("Keep Awake module started.")

    def pause(self):
        self.enabled = False
        self.set_keep_awake(False)
        self.status.setText("PAUSED")
        self.status.setStyleSheet(
            "font-size: 26px; font-weight: 900; color: #EF4444;"
        )
        log("Keep Awake module paused.")

    def refresh_now(self):
        self.set_keep_awake(True)
        now = datetime.now().strftime("%I:%M:%S %p")
        self.last_refresh.setText(f"Last refresh: {now}")
        log("Keep Awake refresh sent.")


class KeepAwakeModule(TRIZModule):
    def info(self):
        return ModuleInfo(
            id="keep_awake",
            name="Keep Awake",
            category="Utilities",
            version="1.1.0",
            author="Trisler Automation",
            description="Windows idle prevention utility.",
            accent="#EF4444",
        )

    def create_page(self):
        return KeepAwakePage()


def create_module(platform=None):
    return KeepAwakeModule(platform)

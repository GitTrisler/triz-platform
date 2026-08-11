from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QPushButton, QProgressBar, QHBoxLayout
from PySide6.QtCore import QTimer
import qtawesome as qta
from core.autocad import acad

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class SectionCard(QFrame):
    def __init__(self, title, icon_name, color):
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(16, 16))
        header.addWidget(icon_label)
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {color};")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        layout.addLayout(self.body)


class ServiceMonitor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        self.acad_card = SectionCard("AutoCAD Connection", "fa5s.plug", "#38BDF8")

        status_row = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_text = QLabel("Connected")
        self.status_text.setStyleSheet("font-weight: 600;")
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_text)
        status_row.addStretch()
        self.acad_card.body.addLayout(status_row)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setObjectName("GhostButton")
        self.disconnect_btn.clicked.connect(self.handle_disconnect)
        self.acad_card.body.addWidget(self.disconnect_btn)

        self.product = QLabel()
        self.drawing = QLabel()
        self.layout_name = QLabel()
        for label in [self.product, self.drawing, self.layout_name]:
            label.setObjectName("Muted")
            label.setWordWrap(True)
            self.acad_card.body.addWidget(label)

        self.sys_card = SectionCard("System Monitor", "fa5s.microchip", "#A78BFA")

        cpu_row = QHBoxLayout()
        cpu_row.addWidget(QLabel("CPU Usage"))
        cpu_row.addStretch()
        self.cpu_value = QLabel("0%")
        cpu_row.addWidget(self.cpu_value)
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setFixedHeight(6)

        mem_row = QHBoxLayout()
        mem_row.addWidget(QLabel("Memory Usage"))
        mem_row.addStretch()
        self.mem_value = QLabel("0%")
        mem_row.addWidget(self.mem_value)
        self.mem_bar = QProgressBar()
        self.mem_bar.setTextVisible(False)
        self.mem_bar.setFixedHeight(6)

        self.sys_card.body.addLayout(cpu_row)
        self.sys_card.body.addWidget(self.cpu_bar)
        self.sys_card.body.addLayout(mem_row)
        self.sys_card.body.addWidget(self.mem_bar)

        version_label = QLabel("TRIZ Platform    v3.2.0")
        version_label.setObjectName("Muted")
        self.sys_card.body.addWidget(version_label)

        self.help_card = SectionCard("Need Help?", "fa5s.question-circle", "#F59E0B")
        self.help_card.body.addWidget(self._help_row("fa5s.book", "User Guide", "Open documentation"))
        self.help_card.body.addWidget(self._help_row("fa5s.play-circle", "Video Tutorials", "Watch step-by-step videos"))
        self.help_card.body.addWidget(self._help_row("fa5s.headset", "Contact Support", "Get help from our team"))

        layout.addWidget(self.acad_card)
        layout.addWidget(self.sys_card)
        layout.addWidget(self.help_card)
        layout.addStretch()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1500)
        self.refresh()

    def _help_row(self, icon_name, title, subtitle):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 4, 0, 4)
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color="#9CA3AF").pixmap(18, 18))
        h.addWidget(icon_label)
        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        t = QLabel(title)
        t.setStyleSheet("font-weight: 600;")
        s = QLabel(subtitle)
        s.setObjectName("Muted")
        text_col.addWidget(t)
        text_col.addWidget(s)
        h.addLayout(text_col)
        h.addStretch()
        return row

    def handle_disconnect(self):
        if hasattr(acad, "disconnect"):
            acad.disconnect()
        self.refresh()

    def refresh(self):
        state = acad.get_state()
        if state.connected:
            self.status_dot.setStyleSheet("color: #22C55E; font-size: 14px;")
            self.status_text.setText("Connected")
            self.product.setText(f"Product: {state.product}")
            self.drawing.setText(f"Drawing: {state.document or 'No Drawing'}")
            self.layout_name.setText(f"Layout: {acad.active_layout_name() or '--'}")
            self.disconnect_btn.setEnabled(True)
        else:
            self.status_dot.setStyleSheet("color: #EF4444; font-size: 14px;")
            self.status_text.setText("Not Connected")
            self.product.setText("Product: --")
            self.drawing.setText("Drawing: --")
            self.layout_name.setText("Layout: --")
            self.disconnect_btn.setEnabled(False)

        if HAS_PSUTIL:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            self.cpu_value.setText(f"{cpu:.0f}%")
            self.cpu_bar.setValue(int(cpu))
            self.mem_value.setText(f"{mem:.0f}%")
            self.mem_bar.setValue(int(mem))
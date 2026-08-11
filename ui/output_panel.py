import html
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QTabWidget,
    QHBoxLayout, QPushButton, QLineEdit, QDialog, QLabel
)
from PySide6.QtGui import QTextCursor, QTextBlockFormat, QColor
from PySide6.QtCore import Qt

from ui.design_system import Colors, level_color


LEVEL_ICONS = {
    "ERROR": "✕",
    "WARNING": "⚠",
    "SUCCESS": "✓",
}

LOG_STYLE = f"""
    QTextEdit {{
        background-color: {Colors.SURFACE};
        border: none;
        font-family: Consolas;
        font-size: 13px;
    }}
    QScrollBar:vertical {{
        background: {Colors.SURFACE};
        width: 12px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {Colors.SURFACE_3};
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {Colors.BORDER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
"""


class OutputPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.entries = {}

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter log...")
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.SURFACE};
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }}
        """)
        self.search_box.textChanged.connect(self.apply_filter)

        self.level_filters = {}
        self.active_levels = set()

        filter_row.addWidget(self.search_box, stretch=1)

        for level in ["INFO", "SUCCESS", "WARNING", "ERROR"]:
            chip = QPushButton(level.capitalize())
            chip.setCheckable(True)
            chip.setChecked(True)
            self.active_levels.add(level)
            color = level_color(level)

            chip.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.SURFACE_2};
                    color: {Colors.MUTED};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 10px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: 700;
                }}
                QPushButton:checked {{
                    background-color: {color};
                    color: {Colors.BG};
                    border: 1px solid {color};
                }}
            """)
            chip.clicked.connect(lambda checked, lv=level: self.toggle_level(lv, checked))
            self.level_filters[level] = chip
            filter_row.addWidget(chip)

        self.expand_btn = QPushButton("⤢ Expand")
        self.expand_btn.setObjectName("GhostButton")
        self.expand_btn.clicked.connect(self.open_expanded_view)
        filter_row.addWidget(self.expand_btn)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabBar::tab {{
                background-color: {Colors.SURFACE_2};
                color: {Colors.MUTED};
                padding: 8px 16px;
                border: 1px solid {Colors.BORDER};
                font-weight: 700;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.SURFACE};
                color: {Colors.TEXT};
                border-bottom: 2px solid {Colors.BLUE};
            }}
        """)

        self.output = self._make_log()
        self.jobs = self._make_log()
        self.notifications = self._make_log()

        self.tabs.addTab(self.output, "Output")
        self.tabs.addTab(self.jobs, "Jobs")
        self.tabs.addTab(self.notifications, "Notifications")
        self.tabs.currentChanged.connect(lambda _: self.apply_filter())

        controls = QHBoxLayout()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("GhostButton")
        copy_btn.clicked.connect(self.copy_current)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("GhostButton")
        clear_btn.clicked.connect(self.clear_current)

        controls.addStretch()
        controls.addWidget(copy_btn)
        controls.addWidget(clear_btn)

        layout.addLayout(filter_row)
        layout.addWidget(self.tabs)
        layout.addLayout(controls)

        self.write("TRIZ Platform console initialized.", "INFO")

    def _make_log(self):
        box = QTextEdit()
        box.setReadOnly(True)
        box.setStyleSheet(LOG_STYLE)
        self.entries[box] = []
        return box

    def timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def _inline_html(self, ts, message, level):
        color = level_color(level)
        safe_message = html.escape(str(message))
        icon = LEVEL_ICONS.get(level, "")
        icon_html = f'{icon}&nbsp;' if icon else ""

        return (
            f'<span style="color:{Colors.MUTED}; font-size:11px;">{ts}</span>'
            '&nbsp;&nbsp;'
            f'<span style="background-color:{color}; color:{Colors.BG}; '
            f'font-weight:800; font-size:11px;">&nbsp;{level}&nbsp;</span>'
            '&nbsp;&nbsp;'
            f'<span style="color:{Colors.TEXT}; font-size:13px; font-weight:'
            f'{"800" if level in ("ERROR", "WARNING") else "400"};">{icon_html}{safe_message}</span>'
        )

    def _write_block(self, box, ts, message, level):
        cursor = box.textCursor()
        cursor.movePosition(QTextCursor.End)

        if not box.document().isEmpty():
            cursor.insertBlock()

        block_format = QTextBlockFormat()
        bg = Colors.SURFACE_2
        if level == "ERROR":
            bg = "#3A1F24"
        elif level == "WARNING":
            bg = "#3A331F"

        block_format.setBackground(QColor(bg))
        block_format.setTopMargin(4)
        block_format.setBottomMargin(4)
        block_format.setLeftMargin(10)
        block_format.setRightMargin(10)
        cursor.setBlockFormat(block_format)

        cursor.insertHtml(self._inline_html(ts, message, level))

    def _append_entry(self, box, message, level):
        ts = self.timestamp()
        self.entries[box].append((ts, message, level))

        if level in self.active_levels and self._matches_search(message):
            self._write_block(box, ts, message, level)
            box.ensureCursorVisible()

    def write(self, message, level="INFO"):
        self._append_entry(self.output, message, level)

    def write_job(self, message, level="JOB"):
        self._append_entry(self.jobs, message, level)

    def notify(self, message, level="NOTICE"):
        self._append_entry(self.notifications, message, level)

    def _matches_search(self, message):
        query = self.search_box.text().strip().lower()
        return query in str(message).lower() if query else True

    def toggle_level(self, level, checked):
        if checked:
            self.active_levels.add(level)
        else:
            self.active_levels.discard(level)
        self.apply_filter()

    def apply_filter(self):
        box = self.tabs.currentWidget()
        if box not in self.entries:
            return

        box.clear()
        for ts, message, level in self.entries[box]:
            if level in self.active_levels and self._matches_search(message):
                self._write_block(box, ts, message, level)
        box.ensureCursorVisible()

    def copy_current(self):
        box = self.tabs.currentWidget()
        if box:
            box.selectAll()
            box.copy()
            cursor = box.textCursor()
            cursor.clearSelection()
            box.setTextCursor(cursor)

    def clear_current(self):
        box = self.tabs.currentWidget()
        if box:
            box.clear()
            self.entries[box] = []

    def open_expanded_view(self):
        box = self.tabs.currentWidget()
        if box not in self.entries:
            return

        tab_name = self.tabs.tabText(self.tabs.currentIndex())

        dialog = QDialog(self)
        dialog.setWindowTitle(f"{tab_name} — Full View")
        dialog.resize(1100, 720)
        dialog.setStyleSheet(f"background-color: {Colors.BG};")

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.setContentsMargins(16, 16, 16, 16)
        dlg_layout.setSpacing(10)

        header = QLabel(f"{tab_name} — {len(self.entries[box])} entries")
        header.setStyleSheet(f"color: {Colors.TEXT}; font-size: 16px; font-weight: 800;")
        dlg_layout.addWidget(header)

        big_log = QTextEdit()
        big_log.setReadOnly(True)
        big_log.setStyleSheet(LOG_STYLE)

        cursor = big_log.textCursor()
        for ts, message, level in self.entries[box]:
            if not big_log.document().isEmpty():
                cursor.movePosition(QTextCursor.End)
                cursor.insertBlock()

            block_format = QTextBlockFormat()
            bg = Colors.SURFACE_2
            if level == "ERROR":
                bg = "#3A1F24"
            elif level == "WARNING":
                bg = "#3A331F"
            block_format.setBackground(QColor(bg))
            block_format.setTopMargin(4)
            block_format.setBottomMargin(4)
            block_format.setLeftMargin(10)
            block_format.setRightMargin(10)
            cursor.setBlockFormat(block_format)
            cursor.insertHtml(self._inline_html(ts, message, level))

        dlg_layout.addWidget(big_log, stretch=1)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("GhostButton")
        close_btn.clicked.connect(dialog.accept)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        dlg_layout.addLayout(btn_row)

        dialog.exec()
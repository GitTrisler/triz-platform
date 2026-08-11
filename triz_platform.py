import os
import sys

# High-DPI configuration must happen before QApplication is created.
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QLineEdit,
    QStackedWidget, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtGui import QShortcut, QKeySequence, QGuiApplication
from PySide6.QtCore import Qt

try:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
except Exception:
    pass

import qtawesome as qta

from core.theme import STYLE
from core.logger import log
from core.settings import load_config
from core.autocad import acad
from core.platform import PlatformAPI
from core.module_registry import ModuleRegistry

from ui.status_bar import TRIZStatusBar
from ui.dock_manager import DockManager
from ui.floating_palette import FloatingCommandPalette
from ui.output_panel import OutputPanel

from modules.dashboard import DashboardPage
from modules.logs import LogsPage
from modules.settings_page import SettingsPage
from modules.placeholders import PlaceholderPage


APP_NAME = "TRIZ Platform"
VERSION = "3.2.0"


class TRIZPlatform(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = load_config()
        self.platform = PlatformAPI(app=self)

        self.page_map = {}
        self.registry = ModuleRegistry(platform=self.platform)
        self.registry.scan()

        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.resize(1360, 820)
        self.setMinimumSize(1180, 720)

        self.output = OutputPanel()

        self.build_ui()
        self.setup_shortcuts()
        self.connect_autocad_status()

        log(f"{APP_NAME} v{VERSION} started.")
        log(f"Registered modules: {len(self.registry.all())}")

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self.build_header())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = self.build_sidebar()
        self.pages = QStackedWidget()

        self.add_pages()

        self.dock = DockManager(self.pages)

        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.dock)

        root_layout.addWidget(body, stretch=1)

        self.status = TRIZStatusBar()
        self.setStatusBar(self.status)

    def setup_shortcuts(self):
        self.command_palette_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.command_palette_shortcut.activated.connect(self.open_command_palette)

    def open_command_palette(self):
        palette = FloatingCommandPalette(
            parent=self,
            registry=self.registry,
            open_callback=self.open_page
        )
        palette.exec()

    def connect_autocad_status(self):
        if acad.connect(visible=True):
            state = acad.get_state()
            drawing = state.document or "No Drawing"
            self.status.set_autocad(f"Connected | {drawing}")
            log(f"AutoCAD connected: {drawing}")

            if hasattr(self, "output"):
                self.output.write(f"AutoCAD connected: {drawing}", "SUCCESS")
        else:
            self.status.set_autocad("Not Connected")
            log(f"AutoCAD not connected: {acad.get_state().error}")

            if hasattr(self, "output"):
                self.output.write("AutoCAD not connected.", "WARNING")

    def build_header(self):
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(64)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 10, 18, 10)

        badge = QLabel("TRIZ")
        badge.setObjectName("TRIZBadge")

        title = QLabel("Platform")
        title.setStyleSheet("font-size: 20px; font-weight: 900;")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search modules or commands...")
        self.search.setFixedWidth(360)
        self.search.returnPressed.connect(self.handle_search)

        notify = QPushButton("Notifications")
        notify.setObjectName("GhostButton")

        user = QLabel(self.config.get("user", "Cody"))
        user.setObjectName("Muted")

        layout.addWidget(badge)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.search)
        layout.addWidget(notify)
        layout.addWidget(user)

        return header

    def build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(280)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setSpacing(10)

        self.nav = QTreeWidget()
        self.nav.setHeaderHidden(True)
        self.nav.setIndentation(12)
        self.nav.itemClicked.connect(self.handle_nav_click)

        self.add_nav_item("Dashboard", "Dashboard", "fa5s.home")

        grouped = self.registry.by_category()
        category_icons = {
            "Drawing Automation": "fa5s.drafting-compass",
            "Utilities": "fa5s.tools",
        }

        for category in sorted(grouped.keys()):
            children = [
                (module.name, module.name, "fa5s.file-alt")
                for module in sorted(grouped[category], key=lambda m: m.name)
            ]
            self.add_nav_section(
                category,
                children,
                category_icons.get(category, "fa5s.folder")
            )

        self.add_nav_section("Administration", [
            ("Logs", "Logs", "fa5s.clipboard-list"),
            ("Settings", "Settings", "fa5s.cog"),
        ], "fa5s.user-shield")

        self.nav.expandAll()
        layout.addWidget(self.nav)

        return sidebar

    def add_nav_item(self, label, page_name, icon_name=None):
        item = QTreeWidgetItem([label])
        item.setData(0, Qt.UserRole, page_name)

        if icon_name:
            item.setIcon(0, qta.icon(icon_name, color="#F9FAFB"))

        self.nav.addTopLevelItem(item)

    def add_nav_section(self, section_name, children, icon_name=None):
        parent = QTreeWidgetItem([section_name.upper()])
        parent.setData(0, Qt.UserRole, None)

        font = parent.font(0)
        font.setPointSize(9)
        font.setBold(True)
        parent.setFont(0, font)

        if icon_name:
            parent.setIcon(0, qta.icon(icon_name, color="#9CA3AF"))

        self.nav.addTopLevelItem(parent)

        for label, page_name, child_icon in children:
            child = QTreeWidgetItem([label])
            child.setData(0, Qt.UserRole, page_name)
            child.setIcon(0, qta.icon(child_icon, color="#F9FAFB"))
            parent.addChild(child)

    def add_pages(self):
        base_pages = [
            ("Dashboard", DashboardPage(
                self.config,
                [module.__dict__ for module in self.registry.all()],
                self.open_page
            )),
            ("Logs", LogsPage(self.output)),
            ("Settings", SettingsPage(self.config)),
        ]

        for name, widget in base_pages:
            index = self.pages.addWidget(widget)
            self.page_map[name] = index

        for module in self.registry.all():
            page = self.registry.create_page(module.name)

            if page is None:
                page = PlaceholderPage(module.name, module.category)

            index = self.pages.addWidget(page)
            self.page_map[module.name] = index

    def handle_nav_click(self, item):
        page_name = item.data(0, Qt.UserRole)

        if not page_name:
            item.setExpanded(not item.isExpanded())
            return

        self.open_page(page_name)

    def open_page(self, page_name):
        if page_name in self.page_map:
            self.pages.setCurrentIndex(self.page_map[page_name])
            self.status.set_module(page_name)
            log(f"Opened module: {page_name}")

            if hasattr(self, "output"):
                self.output.write(f"Opened module: {page_name}", "MODULE")

    def handle_search(self):
        query = self.search.text().strip()

        if not query:
            return

        matches = self.registry.search(query)

        if matches:
            self.open_page(matches[0].name)
            self.search.clear()
            return

        for page_name in self.page_map:
            if query.lower() in page_name.lower():
                self.open_page(page_name)
                self.search.clear()
                return

        self.status.set_module(f"No module found for: {query}")

        if hasattr(self, "output"):
            self.output.write(f"No module found for: {query}", "WARNING")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)

    window = TRIZPlatform()
    window.show()

    sys.exit(app.exec())
"""
TRIZ Project Hub — main window.

Shell layout mirrors the rest of TRIZ Platform: sidebar navigation on the
left, global search in the header, stacked pages in the middle, status strip
at the bottom. Indexing runs on a QThread so a 10,000-file project never
freezes the UI. Everything UI-facing lives here; triz_hub.core has no Qt
imports, so the whole engine lifts straight into the existing platform shell
as a module.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (QEasingCurve, QPropertyAnimation, QSettings,
                            Qt, QThread, QTimer, QUrl, Signal)
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut

try:
    import qtawesome as qta
except ImportError:  # icons are a nicety, not a dependency
    qta = None
from PySide6.QtWidgets import (QFrame, QGraphicsOpacityEffect, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QMainWindow,
                               QStackedWidget, QVBoxLayout, QWidget)

from .theme import PALETTE, build_qss
from ..core.db import Database
from ..core.indexer import Indexer
from .pages.dashboard import DashboardPage
from .pages.lists import DocumentsPage, IssuesPage, ObjectsPage
from .pages.object_detail import ObjectDetailPage
from .pages.search import SearchPage
from .pages.tools import PatternsPage, ToolsPage

NAV = ["Dashboard", "Search", "Objects", "Documents", "Issues", "Tools", "Patterns"]
NAV_ICONS = {"Dashboard": "fa5s.th-large", "Search": "fa5s.search",
             "Objects": "fa5s.cube", "Documents": "fa5s.file-alt",
             "Issues": "fa5s.exclamation-triangle", "Tools": "fa5s.tools",
             "Patterns": "fa5s.code"}


class IndexWorker(QThread):
    progressed = Signal(int, int, str)
    logged = Signal(str, str)
    finished_stats = Signal(dict)
    failed = Signal(str)

    def __init__(self, root: str):
        super().__init__()
        self.root = root

    def run(self):
        try:
            # The worker owns its own connection — sqlite objects don't cross threads.
            ix = Indexer(self.root,
                         progress=lambda d, t, p: self.progressed.emit(d, t, p),
                         log=lambda lvl, m: self.logged.emit(lvl, m))
            stats = ix.run()
            ix.db.close()
            self.finished_stats.emit(stats)
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


class HubShell(QWidget):
    """The whole Project Hub as one embeddable widget.

    Standalone (`run.py`) wraps this in MainWindow; the TRIZ Platform docks it
    as a module page. `platform` is the PlatformAPI when docked (used for
    logging/notifications and to yield Ctrl+K to the command palette);
    `settings` is any object exposing value()/setValue().
    """

    def __init__(self, platform=None, settings=None, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.docked = platform is not None
        self.db: Database | None = None
        self.root: str | None = None
        self.worker: IndexWorker | None = None
        self.settings = settings or QSettings("TRIZ", "ProjectHub")
        self.setStyleSheet(build_qss())

        # ------------------------------------------------------------ shell
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(200)
        side_lay = QVBoxLayout(sidebar)
        side_lay.setContentsMargins(0, 16, 0, 12)
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(18, 2, 14, 0)
        brand_row.setSpacing(10)
        glyph = QLabel()
        if qta:
            glyph.setPixmap(qta.icon("fa5s.drafting-compass",
                                     color=PALETTE["accent"]).pixmap(20, 20))
        wordmark = QVBoxLayout()
        wordmark.setSpacing(0)
        brand = QLabel("TRIZ")
        brand.setStyleSheet("font-size: 15px; font-weight: 800;"
                            f"letter-spacing: 4px; color: {PALETTE['text']};"
                            "background: transparent;")
        brand_sub = QLabel("PROJECT HUB")
        brand_sub.setStyleSheet("font-size: 8px; font-weight: 800;"
                                f"letter-spacing: 3px; color: {PALETTE['muted']};"
                                "background: transparent;")
        wordmark.addWidget(brand)
        wordmark.addWidget(brand_sub)
        brand_row.addWidget(glyph)
        brand_row.addLayout(wordmark)
        brand_row.addStretch()
        brand_hr = QFrame()
        brand_hr.setObjectName("HairlineH")
        nav_cap = QLabel("WORKSPACE")
        nav_cap.setStyleSheet(
            f"color: {PALETTE['faint']}; font-size: 9px; font-weight: 800;"
            "letter-spacing: 2.2px; padding: 10px 20px 4px 20px;"
            "background: transparent;")
        self.nav = QListWidget()
        self.nav.setObjectName("Nav")
        from PySide6.QtCore import QSize
        self.nav.setIconSize(QSize(15, 15))
        for name in NAV:
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(name)
            if qta:
                item.setIcon(qta.icon(NAV_ICONS[name], color="#7C8BA3",
                                      color_active="#38BDF8"))
            self.nav.addItem(item)
        side_lay.addLayout(brand_row)
        side_lay.addSpacing(12)
        side_lay.addWidget(brand_hr)
        side_lay.addWidget(nav_cap)
        side_lay.addWidget(self.nav, stretch=1)
        foot_hr = QFrame()
        foot_hr.setObjectName("HairlineH")
        foot = QHBoxLayout()
        foot.setContentsMargins(20, 10, 16, 4)
        self.side_dot = QLabel("●")
        self.side_dot.setStyleSheet(
            f"color: {PALETTE['faint']}; font-size: 9px; background: transparent;")
        self.side_status = QLabel("No project")
        self.side_status.setStyleSheet(
            f"color: {PALETTE['muted']}; font-size: 10.5px; background: transparent;")
        ver = QLabel("v0.1")
        ver.setStyleSheet(
            f"color: {PALETTE['faint']}; font-size: 9.5px;"
            "font-family: 'Cascadia Code', 'Consolas', monospace;"
            "background: transparent;")
        foot.addWidget(self.side_dot)
        foot.addWidget(self.side_status)
        foot.addStretch()
        foot.addWidget(ver)
        side_lay.addWidget(foot_hr)
        side_lay.addLayout(foot)

        main = QWidget()
        main_lay = QVBoxLayout(main)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        header = QFrame()
        header.setObjectName("Header")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 10, 20, 10)
        crumb = QLabel("PROJECT ▸")
        crumb.setStyleSheet(
            f"color: {PALETTE['faint']}; font-size: 9.5px; font-weight: 800;"
            "letter-spacing: 2px; background: transparent;")
        self.project_label = QLabel("none")
        self.project_label.setStyleSheet(
            f"color: {PALETTE['secondary']}; font-size: 12px; font-weight: 600;"
            "background: transparent;")
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText(
            "Search tags, line numbers, drawings, text…   Ctrl+K")
        self.search_field.setFixedWidth(460)
        if qta:
            self.search_field.addAction(
                qta.icon("fa5s.search", color=PALETTE["muted"]),
                QLineEdit.LeadingPosition)
        self.search_field.returnPressed.connect(self._do_search)
        if qta:
            self._clear_action = self.search_field.addAction(
                qta.icon("fa5s.times-circle", color=PALETTE["muted"]),
                QLineEdit.TrailingPosition)
            self._clear_action.setToolTip("Clear search  (Esc)")
            self._clear_action.triggered.connect(self._clear_search)
            self._clear_action.setVisible(False)
        else:
            self._clear_action = None
            self.search_field.setClearButtonEnabled(True)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(350)
        self._search_timer.timeout.connect(self._do_search)
        self.search_field.textChanged.connect(self._on_search_changed)
        self.search_field.textEdited.connect(self._on_search_edited)
        for seq in (("Ctrl+F",) if self.docked else ("Ctrl+K", "Ctrl+F")):
            sc = QShortcut(QKeySequence(seq), self)
            if self.docked:
                sc.setContext(Qt.WidgetWithChildrenShortcut)
            sc.activated.connect(self._focus_search)
        esc = QShortcut(QKeySequence("Escape"), self.search_field)
        esc.setContext(Qt.WidgetShortcut)
        esc.activated.connect(self._escape_search)
        h_lay.addWidget(crumb)
        h_lay.addWidget(self.project_label)
        h_lay.addStretch()
        h_lay.addWidget(self.search_field)

        # ------------------------------------------------------------ pages
        self.pages = QStackedWidget()
        self.p_dash = DashboardPage()
        self.p_search = SearchPage()
        self.p_objects = ObjectsPage()
        self.p_docs = DocumentsPage()
        self.p_issues = IssuesPage()
        self.p_tools = ToolsPage()
        self.p_patterns = PatternsPage()
        self.p_object_detail = ObjectDetailPage()
        for p in (self.p_dash, self.p_search, self.p_objects, self.p_docs,
                  self.p_issues, self.p_tools, self.p_patterns, self.p_object_detail):
            self.pages.addWidget(p)

        from .widgets import BlueprintFrame
        workspace = BlueprintFrame()
        ws_lay = QVBoxLayout(workspace)
        ws_lay.setContentsMargins(0, 0, 0, 0)
        ws_lay.addWidget(self.pages)
        main_lay.addWidget(header)
        main_lay.addWidget(workspace, stretch=1)
        self.status_line = QLabel("Open a project folder to begin.")
        self.status_line.setObjectName("StatusLine")
        self.status_line.setStyleSheet(
            f"color: {PALETTE['muted']}; font-size: 11.5px;"
            f"border-top: 1px solid {PALETTE['border']};"
            "padding: 5px 14px; background: transparent;")
        main_lay.addWidget(self.status_line)
        outer.addWidget(sidebar)
        outer.addWidget(main, stretch=1)

        # ------------------------------------------------------------ wiring
        self.nav.currentRowChanged.connect(self._nav_changed)
        self.nav.setCurrentRow(0)
        self.p_dash.open_project_requested.connect(self.open_project)
        self.p_dash.index_requested.connect(self.start_index)
        for sig in (self.p_search.open_object, self.p_objects.open_object,
                    self.p_issues.open_object, self.p_object_detail.open_object):
            sig.connect(self.show_object)
        for sig in (self.p_search.open_file, self.p_docs.open_file,
                    self.p_issues.open_file, self.p_object_detail.open_file):
            sig.connect(self.open_in_default_app)
        self.p_search.run_query.connect(self._run_suggestion)
        self.p_tools.status.connect(lambda m: self._status(m, 15000))
        self.p_patterns.status.connect(lambda m: self._status(m, 15000))

        last = self.settings.value("last_project", "")
        if last and Path(last).is_dir():
            self.open_project(last)

    # ---------------------------------------------------------------- project
    def open_project(self, root: str):
        if self.db:
            self.db.close()
        self.root = root
        self.db = Database(root)
        from ..core.patterns import DEFAULT_PATTERNS
        self.db.seed_patterns(DEFAULT_PATTERNS)
        self.settings.setValue("last_project", root)
        self.project_label.setText(Path(root).name)
        self.project_label.setToolTip(root)
        already = self.db.get_meta("last_indexed")
        self._side_status(
            PALETTE["success"] if already else PALETTE["warning"],
            "Index current" if already else "Not indexed")
        last = self.db.get_meta("last_indexed")
        self.p_dash.set_project(root, float(last) if last else None)
        self._refresh_all()
        already = self.db.get_meta("last_indexed")
        self._status(
            "Project opened — index is current." if already
            else "Project opened — run Index Project to build the database.", 10000)

    def _status(self, message: str, timeout: int = 0, level: str = "INFO"):
        """Status text for the strip; mirrored to the platform output panel."""
        self.status_line.setText(message)
        if self.platform is not None:
            self.platform.output_write(message, level)

    def _refresh_all(self):
        if not self.db:
            return
        self.p_dash.set_stats(self.db.stats())
        self.p_dash.set_breakdowns(self.db)
        self.p_objects.set_db(self.db)
        self.p_search.set_db(self.db)
        self.p_docs.set_db(self.db)
        self.p_issues.set_db(self.db)
        self.p_patterns.set_db(self.db)
        self.p_tools.set_context(self.db, self.root)

    # ---------------------------------------------------------------- indexing
    def start_index(self):
        if not self.root or (self.worker and self.worker.isRunning()):
            return
        self.p_dash.indexing_started()
        self.p_dash.log.log("info", "Indexing started…")
        self.worker = IndexWorker(self.root)
        self.worker.progressed.connect(
            lambda d, t, p: self.p_dash.indexing_progress(d, t, p))
        self.worker.logged.connect(self.p_dash.log.log)
        self.worker.finished_stats.connect(self._index_done)
        self.worker.failed.connect(self._index_failed)
        self.worker.start()

    def _fade_to(self, index_or_widget):
        """Page switch with a 160 ms fade-in on the incoming page."""
        if isinstance(index_or_widget, int):
            self.pages.setCurrentIndex(index_or_widget)
        else:
            self.pages.setCurrentWidget(index_or_widget)
        page = self.pages.currentWidget()
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(160)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: page.setGraphicsEffect(None))
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._fade_anim = anim

    def _pulse_start(self):
        self._side_status(PALETTE["accent"], "Indexing…")
        effect = QGraphicsOpacityEffect(self.side_dot)
        self.side_dot.setGraphicsEffect(effect)
        pulse = QPropertyAnimation(effect, b"opacity", self)
        pulse.setStartValue(1.0)
        pulse.setKeyValueAt(0.5, 0.25)
        pulse.setEndValue(1.0)
        pulse.setDuration(1100)
        pulse.setLoopCount(-1)
        pulse.start()
        self._pulse = pulse

    def _pulse_stop(self):
        if getattr(self, "_pulse", None):
            self._pulse.stop()
            self._pulse = None
        self.side_dot.setGraphicsEffect(None)

    def _side_status(self, color: str, text: str):
        self.side_dot.setStyleSheet(
            f"color: {color}; font-size: 9px; background: transparent;")
        self.side_status.setText(text)

    def _index_done(self, stats: dict):
        self._pulse_stop()
        if self.platform is not None:
            self.platform.notify(
                "Project Hub",
                f"Index complete — {stats.get('objects', 0)} objects, "
                f"{stats.get('issues', 0)} issues.", "success")
        self.p_dash.indexing_finished()
        self._side_status(PALETTE["success"], "Index current")
        # Reopen our own connection to pick up the worker's writes.
        self.db = Database(self.root)
        self._refresh_all()
        self._status(
            f"Indexed in {stats.get('seconds', '?')}s — {stats.get('objects', 0)} objects, "
            f"{stats.get('issues', 0)} issues.", 20000)

    def _index_failed(self, msg: str):
        self._pulse_stop()
        if self.platform is not None:
            self.platform.notify("Project Hub", f"Index failed: {msg}", "error")
        self._side_status(PALETTE["error"], "Index failed")
        self.p_dash.indexing_finished()
        self.p_dash.log.log("error", f"Indexing failed: {msg}")

    def _nav_changed(self, row: int):
        self.pages.setCurrentIndex(row)
        if 0 <= row < len(NAV) and NAV[row] == "Search":
            self._focus_search()

    # ---------------------------------------------------------------- actions
    def _focus_search(self):
        self.search_field.setFocus()
        self.search_field.selectAll()

    def _on_search_changed(self, text: str):
        # fires on typing AND programmatic setText — keeps the ✕ in sync
        if self._clear_action is not None:
            self._clear_action.setVisible(bool(text))

    def _on_search_edited(self, text: str):
        # live-search debounce (typing only)
        if len(text.strip()) >= 2:
            self._search_timer.start()
        else:
            self._search_timer.stop()
            if not text.strip():
                self.p_search.show_empty()

    def _clear_search(self):
        self._search_timer.stop()
        self.search_field.clear()
        self.p_search.show_empty()
        self.search_field.setFocus()

    def _escape_search(self):
        if self.search_field.text():
            self._clear_search()
        else:
            self.search_field.clearFocus()

    def _do_search(self):
        q = self.search_field.text().strip()
        if not self.db:
            return
        if not q:
            self.p_search.show_empty()
            return
        import time as _time
        t0 = _time.perf_counter()
        objects = self.db.search_objects(q)
        documents = self.db.search_documents(q)
        texts = self.db.fts_search(q)
        elapsed = (_time.perf_counter() - t0) * 1000
        self.p_search.show_results(q, objects, documents, texts, elapsed)
        self.nav.setCurrentRow(NAV.index("Search"))

    def _run_suggestion(self, tag: str):
        self.search_field.setText(tag)
        self._do_search()

    def show_object(self, tag: str):
        if not self.db:
            return
        self.p_object_detail.show_object(self.db, tag)
        self._fade_to(self.p_object_detail)
        self.nav.clearSelection()

    def open_in_default_app(self, rel_path: str):
        if not rel_path or not self.root:
            return
        full = Path(self.root) / rel_path
        if full.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(full)))
        else:
            self._status(f"File not found: {full}", 8000)


class MainWindow(QMainWindow):
    """Standalone window — hosts the same HubShell the platform docks."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TRIZ · Project Hub")
        self.resize(1360, 860)
        self.shell = HubShell()
        self.setCentralWidget(self.shell)

    def __getattr__(self, name):
        # transparent passthrough so existing tests/tools keep working
        return getattr(self.shell, name)

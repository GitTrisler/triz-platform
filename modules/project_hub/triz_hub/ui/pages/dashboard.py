"""Dashboard on the ModuleWorkspace scaffold: workflow stepper (Select Folder
→ Index → Review & Search), Project + Activity cards in the left column,
metric rail on the right, and the platform progress widget showing the file
currently being indexed."""

from __future__ import annotations

import time

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QGridLayout, QLabel, QLineEdit

from ..module_workspace import ModuleWorkspace
from ..theme import PALETTE
from ..triz_widgets import (TRIZButton, TRIZButtonRow, TRIZCard,
                            TRIZMetricCard, input_row)
from ..theme import DOC_CLASS_COLORS, TYPE_COLORS
from ..triz_widgets import TRIZSectionHeader
from ..widgets import LogView, SegmentBar

STEPS = ["Select Folder", "Index Project", "Review & Search"]


class DashboardPage(ModuleWorkspace):
    open_project_requested = Signal(str)
    index_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(
            "Project Hub",
            "Index a project folder and search every drawing, tag, revision, "
            "and deliverable from one place.",
            steps=STEPS, left_width=6, right_width=3, scroll=False)

        # ---- left: Project card ----
        project = TRIZCard("Project")
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select a project folder to index...")
        self.folder_input.setReadOnly(True)
        project.layout.addLayout(input_row("Project Folder", self.folder_input,
                                           self._pick_folder))
        self.indexed_label = QLabel("")
        self.indexed_label.setStyleSheet(
            f"color: {PALETTE['muted']}; font-size: 11px;")
        project.layout.addWidget(self.indexed_label)
        btn_row = TRIZButtonRow()
        self.btn_index = TRIZButton("Index Project", kind="success")
        self.btn_index.setEnabled(False)
        self.btn_index.clicked.connect(self.index_requested.emit)
        btn_row.addWidget(self.btn_index)
        btn_row.add_stretch_end()
        project.layout.addLayout(btn_row)
        self.add_left(project)

        # ---- left: Activity card ----
        activity = TRIZCard("Activity")
        self.log = LogView()
        self.log.setMinimumHeight(240)
        activity.layout.addWidget(self.log)
        self.add_left(activity, stretch=1)

        # ---- right: metric rail ----
        rail = TRIZCard("Index Summary")
        grid = QGridLayout()
        grid.setSpacing(10)
        self.cards = {
            "files": TRIZMetricCard("Files", "—"),
            "documents": TRIZMetricCard("Documents", "—"),
            "objects": TRIZMetricCard("Objects", "—", color=PALETTE["accent"]),
            "occurrences": TRIZMetricCard("Occurrences", "—"),
            "issues": TRIZMetricCard("Issues", "—"),
            "errors": TRIZMetricCard("Errors", "—"),
        }
        for i, m in enumerate(self.cards.values()):
            grid.addWidget(m, i // 2, i % 2)
        rail.layout.addLayout(grid)
        self.status_metric = TRIZMetricCard("Status", "No project")
        rail.layout.addWidget(self.status_metric)
        rail.layout.addSpacing(4)
        rail.layout.addWidget(TRIZSectionHeader("Composition"))
        doc_cap = QLabel("DOCUMENTS BY CLASS")
        obj_cap = QLabel("OBJECTS BY TYPE")
        for cap in (doc_cap, obj_cap):
            cap.setStyleSheet(
                f"color: {PALETTE['faint']}; font-size: 8.5px; font-weight: 800;"
                "letter-spacing: 1.3px; background: transparent;")
        self.class_bar = SegmentBar()
        self.type_bar = SegmentBar()
        rail.layout.addWidget(doc_cap)
        rail.layout.addWidget(self.class_bar)
        rail.layout.addSpacing(2)
        rail.layout.addWidget(obj_cap)
        rail.layout.addWidget(self.type_bar)
        self.add_right(rail)
        self.add_right_stretch()

    def _pick_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select project folder")
        if d:
            self.open_project_requested.emit(d)

    # -- state hooks --------------------------------------------------------
    def set_project(self, path: str, last_indexed: float | None = None):
        self.folder_input.setText(path)
        self.btn_index.setEnabled(True)
        if last_indexed:
            self.indexed_label.setText(
                "Last indexed " + time.strftime("%Y-%m-%d %H:%M",
                                                time.localtime(last_indexed)))
            self.status_metric.set_value("Ready", PALETTE["success"])
            self.set_active_step(3)
        else:
            self.indexed_label.setText("Never indexed — run Index Project.")
            self.status_metric.set_value("Not indexed", PALETTE["warning"])
            self.set_active_step(2)

    def set_stats(self, stats: dict):
        for key, card in self.cards.items():
            card.set_value(stats.get(key, "—"))
        issues = stats.get("issues", 0) or 0
        errors = stats.get("errors", 0) or 0
        self.cards["objects"].set_value(stats.get("objects", "—"), PALETTE["accent"])
        self.cards["issues"].set_value(
            issues, PALETTE["warning"] if issues else PALETTE["text"])
        self.cards["errors"].set_value(
            errors, PALETTE["error"] if errors else PALETTE["success"])

    def indexing_started(self):
        self.btn_index.setEnabled(False)
        self.set_active_step(2)
        self.status_metric.set_value("Indexing…", PALETTE["job"])
        self.update_progress(0, 1, "Indexing", "")

    def indexing_progress(self, done: int, total: int, current_item: str = ""):
        self.update_progress(done, total, "Indexing", current_item)

    def indexing_finished(self):
        self.btn_index.setEnabled(True)
        self.reset_progress()
        self.indexed_label.setText(
            "Last indexed " + time.strftime("%Y-%m-%d %H:%M"))
        self.status_metric.set_value("Complete", PALETTE["success"])
        self.set_active_step(3)

    def set_breakdowns(self, db):
        self.class_bar.set_data(
            [(name, count, DOC_CLASS_COLORS.get(name, PALETTE["muted"]))
             for name, count in db.class_breakdown()])
        self.type_bar.set_data(
            [(name, count, TYPE_COLORS.get(name, PALETTE["muted"]))
             for name, count in db.type_breakdown()])

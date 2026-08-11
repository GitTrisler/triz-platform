"""Documents / Objects / Issues list pages — filterable tables over the index.
Issues page uses severity filter chips, same interaction as the OutputPanel
level chips in the Deliverable Publisher."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QLabel, QLineEdit, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from ..theme import DOC_CLASS_COLORS, PALETTE, SEVERITY_COLORS, TYPE_COLORS
from ..triz_widgets import TRIZMetricCard
from ..widgets import Chip, colored_item, hbox, make_table, stretch_column


class DocumentsPage(QWidget):
    open_file = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(10)
        title = QLabel("Documents")
        title.setObjectName("Title")
        sub = QLabel("Every document the index found, with revision and source.")
        sub.setObjectName("Subtitle")
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter by number, title, or file…")
        self.latest_only = QCheckBox("Latest revisions only")
        self.latest_only.setChecked(True)
        self.table = make_table(["Document No", "Rev", "Title", "Class", "Source", "File"])
        stretch_column(self.table, 2)
        self.table.cellDoubleClicked.connect(
            lambda r, c: self.open_file.emit(self.table.item(r, 5).data(Qt.UserRole)))
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addLayout(hbox(self.filter, self.latest_only, "stretch"))
        lay.addWidget(self.table, stretch=1)
        self._db = None
        self.filter.textChanged.connect(self.refresh)
        self.latest_only.toggled.connect(self.refresh)

    def set_db(self, db):
        self._db = db
        self.refresh()

    def refresh(self):
        if not self._db:
            return
        q = self.filter.text().strip()
        rows = (self._db.latest_documents() if self.latest_only.isChecked()
                else self._db.documents_list(q))
        if self.latest_only.isChecked() and q:
            ql = q.lower()
            rows = [r for r in rows if ql in (r["doc_number"] or "").lower()
                    or ql in (r["title"] or "").lower() or ql in r["name"].lower()]
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for i, d in enumerate(rows):
            self.table.insertRow(i)
            self.table.setItem(i, 0, colored_item(d["doc_number"] or "", mono=True))
            self.table.setItem(i, 1, QTableWidgetItem(d["revision"] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(d["title"] or ""))
            cls = d["doc_class"] or "general"
            self.table.setItem(i, 3, colored_item(
                cls.replace("_", " ").upper(),
                DOC_CLASS_COLORS.get(cls, PALETTE["muted"])))
            self.table.setItem(i, 4, colored_item(d["source"] or "", PALETTE["muted"]))
            fitem = QTableWidgetItem(d["name"])
            fitem.setData(Qt.UserRole, d["path"])
            fitem.setToolTip(d["path"])
            self.table.setItem(i, 5, fitem)
        self.table.setSortingEnabled(True)
        for col in (0, 1, 3, 4):
            self.table.resizeColumnToContents(col)


class ObjectsPage(QWidget):
    open_object = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(10)
        title = QLabel("Objects")
        title.setObjectName("Title")
        sub = QLabel("Every tag in the project — equipment, lines, valves, instruments.")
        sub.setObjectName("Subtitle")
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter tags…")
        self.table = make_table(["Tag", "Type", "In Model", "Occurrences"])
        self.table.cellDoubleClicked.connect(
            lambda r, c: self.open_object.emit(self.table.item(r, 0).text()))
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addWidget(self.filter)
        lay.addWidget(self.table, stretch=1)
        self._db = None
        self.filter.textChanged.connect(self.refresh)

    def set_db(self, db):
        self._db = db
        self.refresh()

    def refresh(self):
        if not self._db:
            return
        rows = self._db.objects_list(self.filter.text().strip())
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for i, o in enumerate(rows):
            self.table.insertRow(i)
            tcolor = TYPE_COLORS.get(o["type"], PALETTE["text"])
            self.table.setItem(i, 0, colored_item(o["tag"], tcolor, mono=True))
            self.table.setItem(i, 1, colored_item(o["type"], tcolor))
            self.table.setItem(i, 2, colored_item(
                "yes" if o["in_model"] else "", PALETTE["success"]))
            self.table.setItem(i, 3, QTableWidgetItem(str(o["hits"])))
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()


class IssuesPage(QWidget):
    open_object = Signal(str)
    open_file = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(10)
        title = QLabel("Issues")
        title.setObjectName("Title")
        sub = QLabel("Live findings from the rule engine — rebuilt on every index.")
        sub.setObjectName("Subtitle")
        self.metrics = {
            "error": TRIZMetricCard("Errors", "0", SEVERITY_COLORS["error"]),
            "warning": TRIZMetricCard("Warnings", "0", SEVERITY_COLORS["warning"]),
            "info": TRIZMetricCard("Info", "0", SEVERITY_COLORS["info"]),
        }
        metric_row = hbox(*self.metrics.values(), "stretch", spacing=14)
        self.chips = {s: Chip(s.capitalize()) for s in ("error", "warning", "info")}
        chip_row = hbox(*self.chips.values(), "stretch")
        self.table = make_table(["Severity", "Category", "Message", "File", "Tag"])
        stretch_column(self.table, 2)
        self.table.cellDoubleClicked.connect(self._activate)
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addLayout(metric_row)
        lay.addLayout(chip_row)
        lay.addWidget(self.table, stretch=1)
        self._db = None
        for c in self.chips.values():
            c.toggled.connect(self.refresh)

    def _activate(self, r, c):
        tag = self.table.item(r, 4).text()
        path = self.table.item(r, 3).data(Qt.UserRole)
        if tag:
            self.open_object.emit(tag)
        elif path:
            self.open_file.emit(path)

    def set_db(self, db):
        self._db = db
        self.refresh()

    def refresh(self):
        if not self._db:
            return
        all_rows = self._db.issues_list()
        for sev, card in self.metrics.items():
            card.set_value(sum(1 for r in all_rows if r["severity"] == sev))
        active = {s for s, c in self.chips.items() if c.isChecked()}
        rows = [r for r in all_rows if r["severity"] in active]
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for i, r in enumerate(rows):
            self.table.insertRow(i)
            self.table.setItem(i, 0, colored_item(
                r["severity"].upper(), SEVERITY_COLORS.get(r["severity"])))
            self.table.setItem(i, 1, QTableWidgetItem(r["category"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["message"]))
            fitem = QTableWidgetItem(r["name"] or "")
            fitem.setData(Qt.UserRole, r["path"])
            self.table.setItem(i, 3, fitem)
            self.table.setItem(i, 4, colored_item(r["tag"] or "", mono=True))
        self.table.setSortingEnabled(True)
        for col in (0, 1, 3, 4):
            self.table.resizeColumnToContents(col)

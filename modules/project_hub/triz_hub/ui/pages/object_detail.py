"""Object detail — click P-101 and see everything connected to that pump:
every drawing, page, spreadsheet row, vendor doc, and site photo, plus the
objects it keeps company with (co-occurrence relationships).
Double-click any occurrence to open the file."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from ..graph_view import RelationGraph
from ..theme import DOC_CLASS_COLORS, PALETTE, SEVERITY_COLORS, TYPE_COLORS
from ..triz_widgets import TRIZCard, TRIZMetricCard, TRIZSectionHeader
from ..widgets import (TagBadge, colored_item, make_table,
                       stretch_column, type_badge)


class ObjectDetailPage(QWidget):
    open_object = Signal(str)
    open_file = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(28, 24, 28, 24)
        self.lay.setSpacing(12)

        self.head_row = QHBoxLayout()
        self.tag_label = QLabel("—")
        self.tag_label.setObjectName("TagHeader")
        self.head_row.addWidget(self.tag_label)
        self.head_row.addStretch()
        self.lay.addLayout(self.head_row)
        self._badges = []

        self.summary = QLabel("")
        self.summary.setObjectName("Muted")
        self.lay.addWidget(self.summary)

        metric_row = QHBoxLayout()
        metric_row.setSpacing(14)
        self.m_occ = TRIZMetricCard("Occurrences", "0", PALETTE["accent"])
        self.m_files = TRIZMetricCard("Files", "0", PALETTE["accent"])
        self.m_related = TRIZMetricCard("Related", "0", PALETTE["success"])
        self.m_issues = TRIZMetricCard("Open Issues", "0", PALETTE["muted"])
        for m in (self.m_occ, self.m_files, self.m_related, self.m_issues):
            metric_row.addWidget(m)
        metric_row.addStretch()
        self.lay.addLayout(metric_row)

        split = QHBoxLayout()
        split.setSpacing(14)

        graph_card = TRIZCard("Relationship Graph")
        hint = QLabel("Objects sharing sheets with this one — click any node "
                      "to traverse the plant")
        hint.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 11px;"
                           "background: transparent;")
        self.graph = RelationGraph()
        self.graph.open_object.connect(self.open_object.emit)
        graph_card.layout.addWidget(hint)
        graph_card.layout.addWidget(self.graph, stretch=1)
        split.addWidget(graph_card, stretch=5)

        occ_col = QVBoxLayout()
        occ_col.setSpacing(10)
        occ_cap = TRIZSectionHeader("Occurrences")
        occ_col.addWidget(occ_cap)
        self.t_occ = make_table(["Class", "File", "Location", "Context"])
        self.t_occ.cellDoubleClicked.connect(self._open_occurrence)
        stretch_column(self.t_occ, 3)
        occ_col.addWidget(self.t_occ, stretch=1)
        split.addLayout(occ_col, stretch=6)

        self.lay.addLayout(split, stretch=1)

        self.issue_cap = TRIZSectionHeader("Open Issues")
        self.t_issues = make_table(["Severity", "Category", "Message"])
        stretch_column(self.t_issues, 2)
        self.lay.addWidget(self.issue_cap)
        self.lay.addWidget(self.t_issues)

    def _open_occurrence(self, r, c):
        item = self.t_occ.item(r, 1)
        if item:
            self.open_file.emit(item.data(Qt.UserRole))

    def show_object(self, db, tag: str):
        obj = db.object_by_tag(tag)
        if not obj:
            self.tag_label.setText(f"{tag} — not found in index")
            self.summary.setText("")
            return
        self.tag_label.setText(obj["tag"])
        self.tag_label.setStyleSheet(
            f"color: {TYPE_COLORS.get(obj['type'], PALETTE['text'])};"
            "font-size: 28px; font-weight: 900;"
            "font-family: 'Cascadia Code', 'Consolas', monospace;")

        for b in self._badges:
            b.setParent(None)
        self._badges = [type_badge(obj["type"])]
        if obj["in_model"]:
            self._badges.append(TagBadge("in model", PALETTE["success"]))
        for b in self._badges:
            self.head_row.insertWidget(self.head_row.count() - 1, b)

        # constellation
        related = db.related_objects(obj["id"])
        self.m_related.set_value(len(related))
        self.graph.show_relations(db, obj["tag"])

        # occurrences
        occ = db.object_occurrences(obj["id"])
        n_files = len({r["path"] for r in occ})
        self.summary.setText("Double-click any occurrence row to open the file")
        self.m_occ.set_value(len(occ))
        self.m_files.set_value(n_files)
        self.t_occ.setSortingEnabled(False)
        self.t_occ.setRowCount(0)
        for i, r in enumerate(occ):
            self.t_occ.insertRow(i)
            cls = r["doc_class"] or "general"
            self.t_occ.setItem(i, 0, colored_item(
                cls.replace("_", " ").upper(),
                DOC_CLASS_COLORS.get(cls, PALETTE["muted"])))
            fi = QTableWidgetItem(r["name"])
            fi.setData(Qt.UserRole, r["path"])
            fi.setToolTip(r["path"])
            self.t_occ.setItem(i, 1, fi)
            self.t_occ.setItem(i, 2, QTableWidgetItem(r["location"] or ""))
            self.t_occ.setItem(i, 3, colored_item(
                (r["context"] or "").replace("\n", " "), PALETTE["muted"]))
        self.t_occ.setSortingEnabled(True)
        for col in (0, 1, 2):
            self.t_occ.resizeColumnToContents(col)

        # issues on this object
        issues = [i for i in db.issues_list() if i["tag"] == obj["tag"]]
        self.m_issues.set_value(
            len(issues),
            PALETTE["warning"] if issues else PALETTE["success"])
        self.issue_cap.setVisible(bool(issues))
        self.t_issues.setVisible(bool(issues))
        self.t_issues.setRowCount(0)
        for i, r in enumerate(issues):
            self.t_issues.insertRow(i)
            self.t_issues.setItem(i, 0, colored_item(
                r["severity"].upper(), SEVERITY_COLORS.get(r["severity"])))
            self.t_issues.setItem(i, 1, QTableWidgetItem(r["category"]))
            self.t_issues.setItem(i, 2, QTableWidgetItem(r["message"]))
        for col in (0, 1):
            self.t_issues.resizeColumnToContents(col)

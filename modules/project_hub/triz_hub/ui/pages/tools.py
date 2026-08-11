"""Tools — drawing register, deliverable package, revision compare.
Patterns — the per-project tag grammar, editable with a live tester."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QDialog, QFileDialog, QGridLayout, QLabel,
                               QLineEdit, QPlainTextEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget, QAbstractItemView)

from ...core.compare import compare_pdfs
from ...core.extract_pdf import inspect_titleblock
from ...core.package import build_package
from ...core.patterns import TagMatcher
from ...core.register import default_register_name, generate_register
from ..module_workspace import ModuleWorkspace
from ..triz_widgets import (TRIZButton, TRIZButtonRow, TRIZCard,
                            triz_page_header)
from ..widgets import hbox


class ToolsPage(QWidget):
    status = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = None
        self._root = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)
        title, sub = triz_page_header(
            "Tools",
            "Registers, packages, comparisons, and diagnostics built on the index.")
        lay.addWidget(title)
        lay.addWidget(sub)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.addWidget(self._card(
            "Drawing Register",
            "Excel register generated straight from the index: latest revisions, "
            "object index, and live issues. It can't drift from the folder.",
            "Generate Register…", self._gen_register, kind="success"), 0, 0)
        grid.addWidget(self._card(
            "Deliverable Package",
            "Copies the newest revision of every document into a dated folder "
            "with a transmittal sheet.",
            "Build Package…", self._build_package), 0, 1)
        grid.addWidget(self._card(
            "Revision Compare",
            "Overlay two PDF revisions: removed content in red, added in blue, "
            "with a change ratio per sheet.",
            "Compare Two PDFs…", self._compare), 1, 0)
        grid.addWidget(self._card(
            "Title Block Inspector",
            "See exactly what text the indexer finds in a sheet's title block "
            "regions and what it parsed — the fast way to tune extraction for "
            "a new client border.",
            "Inspect a PDF…", self._inspect_tb), 1, 1)
        lay.addLayout(grid)
        lay.addStretch()

    def _card(self, title, desc, btn_text, slot, kind="primary"):
        card = TRIZCard(title)
        d = QLabel(desc)
        d.setObjectName("Muted")
        d.setWordWrap(True)
        b = TRIZButton(btn_text, kind=kind)
        b.clicked.connect(slot)
        row = TRIZButtonRow()
        row.addWidget(b)
        row.add_stretch_end()
        card.layout.addWidget(d)
        card.layout.addStretch()
        card.layout.addLayout(row)
        return card

    def set_context(self, db, root):
        self._db = db
        self._root = root

    def _need_project(self) -> bool:
        if not self._db:
            self.status.emit("Open and index a project first.")
            return True
        return False

    def _gen_register(self):
        if self._need_project():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save register",
                                              default_register_name(),
                                              "Excel (*.xlsx)")
        if path:
            out = generate_register(self._db, path)
            self.status.emit(f"Register written: {out}")

    def _build_package(self):
        if self._need_project():
            return
        d = QFileDialog.getExistingDirectory(self, "Package destination folder")
        if d:
            res = build_package(self._db, self._root, d)
            self.status.emit(
                f"Package built: {res['folder']} — {res['copied']} files copied"
                + (f", {res['skipped']} skipped (no matching file)" if res['skipped'] else ""))

    def _compare(self):
        old, _ = QFileDialog.getOpenFileName(self, "Old revision PDF", "", "PDF (*.pdf)")
        if not old:
            return
        new, _ = QFileDialog.getOpenFileName(self, "New revision PDF",
                                             str(Path(old).parent), "PDF (*.pdf)")
        if not new:
            return
        out = QFileDialog.getExistingDirectory(self, "Output folder for overlays")
        if not out:
            return
        res = compare_pdfs(old, new, out)
        worst = max(res["pages"], key=lambda p: p["changed_ratio"], default=None)
        msg = f"Compared {len(res['pages'])} page(s) → {res['out_dir']}"
        if worst:
            msg += f" — most changed: page {worst['page']} ({worst['changed_ratio']*100:.1f}%)"
        self.status.emit(msg)


    def _inspect_tb(self):
        path, _ = QFileDialog.getOpenFileName(self, "PDF to inspect", "", "PDF (*.pdf)")
        if not path:
            return
        try:
            res = inspect_titleblock(path)
        except Exception as e:
            self.status.emit(f"Inspection failed: {type(e).__name__}: {e}")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Title Block Inspector — {path.rsplit('/', 1)[-1]}")
        dlg.resize(760, 620)
        v = QVBoxLayout(dlg)
        if res["encrypted"]:
            summary = "This PDF is password protected — no text can be read."
        elif res["doc_number"]:
            summary = (f"Parsed:  DOC {res['doc_number']}   "
                       f"REV {res['revision'] or '—'}   "
                       f"TITLE {res['title'] or '—'}   [{res['source']}]")
        else:
            summary = ("Nothing parsed — the labels below don't match the known "
                       "patterns. Tune _parse_tb_text / _regions in "
                       "triz_hub/core/extract_pdf.py for this border.")
        lab = QLabel(summary)
        lab.setWordWrap(True)
        lab.setObjectName("H2")
        v.addWidget(lab)
        box = QPlainTextEdit()
        box.setReadOnly(True)
        chunks = []
        for r in res["regions"]:
            chunks.append(f"───── region: {r['name']} ─────")
            chunks.append(r["text"].strip() or "(no text found in this region)")
            chunks.append("")
        box.setPlainText("\n".join(chunks))
        v.addWidget(box, stretch=1)
        dlg.exec()


class PatternsPage(ModuleWorkspace):
    """Tag grammar editor. Every client numbers things differently — this is
    where a project's conventions live, with a paste-and-test box so a new
    pattern is verified before the next index."""

    status = Signal(str)

    def __init__(self, parent=None):
        super().__init__(
            "Tag Patterns",
            "Regex patterns that turn raw text into project objects. Higher "
            "priority wins on overlap — changes apply on the next index.",
            left_width=6, right_width=3, scroll=False, show_progress=False)
        self._db = None

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Enabled", "Name", "Type", "Regex", "Priority"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        btn_add = TRIZButton("Add Pattern", kind="ghost")
        btn_del = TRIZButton("Remove Selected", kind="ghost")
        btn_save = TRIZButton("Save Patterns", kind="primary")
        btn_add.clicked.connect(self._add_row)
        btn_del.clicked.connect(self._del_row)
        btn_save.clicked.connect(self._save)

        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText('Paste sample text to test, e.g.  PUMP P-101A ON 6"-P-1001-CS150 W/ PT-101')
        self.test_output = QLabel("")
        self.test_output.setObjectName("Muted")
        self.test_output.setWordWrap(True)
        self.test_input.textChanged.connect(self._run_test)

        table_card = TRIZCard("Patterns")
        table_card.layout.addWidget(self.table)
        table_card.layout.addLayout(hbox(btn_add, btn_del, "stretch", btn_save))
        self.add_left(table_card, stretch=1)

        tester = TRIZCard("Pattern Tester")
        tester.layout.addWidget(self.test_input)
        tester.layout.addWidget(self.test_output)
        self.add_right(tester)

        tips = TRIZCard("How Matching Works")
        for t in ("Higher priority wins when matches overlap — PT-101 stays an "
                  "instrument instead of splitting into equipment T-101.",
                  "Suffix letters must be attached (P-101A). A space between "
                  "the tag and the next token is a boundary.",
                  "Disable noisy patterns per project instead of deleting them."):
            tip = QLabel(f'<span style="color:#38BDF8">▸</span>&nbsp; {t}')
            tip.setWordWrap(True)
            tip.setObjectName("Muted")
            tips.layout.addWidget(tip)
        self.add_right(tips)
        self.add_right_stretch()

    def set_db(self, db):
        self._db = db
        self.table.setRowCount(0)
        for p in db.get_patterns(enabled_only=False):
            self._append(bool(p["enabled"]), p["name"], p["object_type"],
                         p["regex"], p["priority"])

    def _append(self, enabled, name, otype, regex, priority):
        r = self.table.rowCount()
        self.table.insertRow(r)
        chk = QTableWidgetItem()
        chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        chk.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
        self.table.setItem(r, 0, chk)
        for c, v in enumerate([name, otype, regex, str(priority)], start=1):
            self.table.setItem(r, c, QTableWidgetItem(v))
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(3, 420)
        from PySide6.QtWidgets import QHeaderView
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def _add_row(self):
        self._append(True, "New pattern", "equipment", r"\bXX-\d{3,4}\b", 50)

    def _del_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)

    def _rows(self):
        out = []
        for r in range(self.table.rowCount()):
            try:
                priority = int(self.table.item(r, 4).text())
            except (ValueError, AttributeError):
                priority = 50
            out.append({
                "enabled": 1 if self.table.item(r, 0).checkState() == Qt.Checked else 0,
                "name": self.table.item(r, 1).text(),
                "object_type": self.table.item(r, 2).text().strip().lower(),
                "regex": self.table.item(r, 3).text(),
                "priority": priority,
            })
        return out

    def _save(self):
        if not self._db:
            self.status.emit("Open a project first — patterns are stored per project.")
            return
        self._db.save_patterns(self._rows())
        self.status.emit("Patterns saved. Re-index to apply.")

    def _run_test(self, text):
        if not text.strip():
            self.test_output.setText("")
            return
        rows = [r for r in self._rows() if r["enabled"]]
        matcher = TagMatcher(rows)
        found = matcher.find(text.upper())
        if found:
            self.test_output.setText("Matches:  " + "   ".join(
                f"{t.tag} ({t.object_type})" for t in found))
        else:
            self.test_output.setText("No matches.")

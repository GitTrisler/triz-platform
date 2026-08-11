"""Search — two proper states on a QStackedWidget.

Empty state: centered hero with a search glyph and live suggestion chips
pulled from the index (top objects by occurrence count), so the page teaches
its own query surface. Fixes the layout bug where hidden result tables let
the labels drift down the page.

Results state: summary line with count + timing, exclusive filter chips
(All / Objects / Documents / Text), each section framed in a TRIZCard with a
count pill, and FTS snippets rendered with the matched query highlighted in
accent via a rich-text delegate.
"""

from __future__ import annotations

import html

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAbstractTextDocumentLayout, QPalette, QTextDocument
from PySide6.QtWidgets import (QButtonGroup, QHBoxLayout, QLabel,
                               QStackedWidget, QStyle, QStyledItemDelegate,
                               QStyleOptionViewItem, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from ..theme import PALETTE, TYPE_COLORS
from ..triz_widgets import TRIZCard, TRIZSectionHeader, triz_page_header
from ..widgets import Chip, FlowLayout, colored_item, make_table, stretch_column

try:
    import qtawesome as qta
except ImportError:
    qta = None


class SnippetHighlightDelegate(QStyledItemDelegate):
    """Renders FTS snippets with [bracketed] matches in bold accent color."""

    def _doc(self, text: str, option) -> QTextDocument:
        out = []
        for i, part in enumerate(html.escape(text).split("[")):
            if i == 0:
                out.append(part)
                continue
            if "]" in part:
                hit, rest = part.split("]", 1)
                out.append(f'<span style="color:{PALETTE["accent"]};'
                           f'font-weight:700">{hit}</span>{rest}')
            else:
                out.append(part)
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setHtml(f'<span style="color:{PALETTE["muted"]}">{"".join(out)}</span>')
        doc.setTextWidth(option.rect.width())
        return doc

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        text, opt.text = opt.text, ""
        style = opt.widget.style() if opt.widget else None
        if style:
            style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)
        doc = self._doc(text, opt)
        painter.save()
        painter.translate(opt.rect.left() + 6,
                          opt.rect.top() + max(0, (opt.rect.height()
                                                   - doc.size().height()) / 2))
        ctx = QAbstractTextDocumentLayout.PaintContext()
        ctx.palette = opt.palette
        ctx.palette.setColor(QPalette.Text, Qt.white)
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 30)


def _count_pill(n: int) -> QLabel:
    pill = QLabel(str(n))
    pill.setStyleSheet(
        f"background: {PALETTE['accent_dim']}; color: {PALETTE['accent_hi']};"
        "border-radius: 9px; padding: 1px 10px; font-size: 11px; font-weight: 800;")
    return pill


class _Section(TRIZCard):
    """TRIZCard with a header row: section title + count pill + table."""

    def __init__(self, title: str, table):
        super().__init__()
        head = QHBoxLayout()
        head.setSpacing(10)
        head.addWidget(TRIZSectionHeader(title))
        self.pill = _count_pill(0)
        head.addWidget(self.pill)
        head.addStretch()
        self.layout.addLayout(head)
        self.layout.addWidget(table)

    def set_count(self, n: int):
        self.pill.setText(str(n))


class SearchPage(QWidget):
    open_object = Signal(str)
    open_file = Signal(str)
    run_query = Signal(str)   # suggestion chip clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 18)
        outer.setSpacing(12)

        self.header, self.sub = triz_page_header(
            "Search", "Objects, documents, and full-text mentions in one query.")
        outer.addWidget(self.header)
        outer.addWidget(self.sub)

        self.stack = QStackedWidget()
        outer.addWidget(self.stack, stretch=1)
        self.stack.addWidget(self._build_empty_state())    # 0
        self.stack.addWidget(self._build_results_state())  # 1
        self.stack.setCurrentIndex(0)

    # ------------------------------------------------------------ empty state
    def _build_empty_state(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addStretch(3)

        if qta:
            icon = QLabel()
            icon.setPixmap(qta.icon("fa5s.search",
                                    color=PALETTE["border_hi"]).pixmap(72, 72))
            icon.setAlignment(Qt.AlignCenter)
            lay.addWidget(icon)

        big = QLabel("Search the project")
        big.setAlignment(Qt.AlignCenter)
        big.setStyleSheet("font-size: 20px; font-weight: 900;")
        hint = QLabel("Any tag, line number, drawing number, or free text — "
                      "press Ctrl+K from anywhere.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setObjectName("Muted")
        lay.addWidget(big)
        lay.addWidget(hint)
        lay.addSpacing(16)

        self.sugg_caption = QLabel("TRY ONE OF THESE")
        self.sugg_caption.setAlignment(Qt.AlignCenter)
        self.sugg_caption.setStyleSheet(
            f"color: {PALETTE['muted']}; font-size: 10px; font-weight: 800;"
            "letter-spacing: 2px;")
        lay.addWidget(self.sugg_caption)
        lay.addSpacing(6)

        self.sugg_row = QHBoxLayout()
        self.sugg_row.setSpacing(8)
        self.sugg_row.addStretch()
        self.sugg_row.addStretch()
        lay.addLayout(self.sugg_row)

        self.no_results = QLabel("")
        self.no_results.setAlignment(Qt.AlignCenter)
        self.no_results.setStyleSheet(
            f"color: {PALETTE['warning']}; font-weight: 700; padding-top: 14px;")
        lay.addWidget(self.no_results)

        lay.addStretch(4)
        return page

    def set_db(self, db):
        """Populate suggestion chips with the index's busiest objects."""
        self._db = db
        while self.sugg_row.count() > 2:
            item = self.sugg_row.takeAt(1)
            if item.widget():
                item.widget().setParent(None)
        objs = sorted(db.objects_list(), key=lambda o: -o["hits"])[:6] if db else []
        for o in objs:
            chip = Chip(o["tag"], checked=False)
            chip.setCheckable(False)
            color = TYPE_COLORS.get(o["type"], PALETTE["muted"])
            chip.setStyleSheet(
                f"QPushButton {{ color: {color}; border: 1px solid {PALETTE['border_hi']};"
                f"border-radius: 12px; padding: 4px 14px; background: {PALETTE['panel']};"
                "font-family: Consolas, monospace; font-size: 12px; font-weight: 700; }"
                f"QPushButton:hover {{ border-color: {color}; background: {PALETTE['panel_hi']}; }}")
            chip.clicked.connect(lambda _=False, t=o["tag"]: self.run_query.emit(t))
            self.sugg_row.insertWidget(self.sugg_row.count() - 1, chip)
        has = bool(objs)
        self.sugg_caption.setVisible(has)

    # ---------------------------------------------------------- results state
    def _build_results_state(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        top = QHBoxLayout()
        self.summary = QLabel("")
        self.summary.setObjectName("Muted")
        top.addWidget(self.summary)
        top.addStretch()
        self.chip_all = Chip("All", checked=True)
        self.chip_obj = Chip("Objects", checked=False)
        self.chip_doc = Chip("Documents", checked=False)
        self.chip_txt = Chip("Text", checked=False)
        group = QButtonGroup(self)
        group.setExclusive(True)
        for c in (self.chip_all, self.chip_obj, self.chip_doc, self.chip_txt):
            group.addButton(c)
            top.addWidget(c)
            c.toggled.connect(self._apply_filter)
        lay.addLayout(top)

        self.t_obj = make_table(["Tag", "Type", "In Model", "Occurrences"])
        self.t_obj.cellDoubleClicked.connect(
            lambda r, c: self.open_object.emit(self.t_obj.item(r, 0).text()))
        self.t_doc = make_table(["Document No", "Rev", "Title", "File"])
        stretch_column(self.t_doc, 2)
        self.t_doc.cellDoubleClicked.connect(
            lambda r, c: self.open_file.emit(self.t_doc.item(r, 3).data(Qt.UserRole)))
        self.t_txt = make_table(["File", "Page", "Snippet"])
        stretch_column(self.t_txt, 2)
        self.t_txt.setItemDelegateForColumn(2, SnippetHighlightDelegate(self.t_txt))
        self.t_txt.cellDoubleClicked.connect(
            lambda r, c: self.open_file.emit(self.t_txt.item(r, 0).data(Qt.UserRole)))

        self.sec_obj = _Section("Objects", self.t_obj)
        self.sec_doc = _Section("Documents", self.t_doc)
        self.sec_txt = _Section("Text Mentions", self.t_txt)
        lay.addWidget(self.sec_obj, stretch=2)
        lay.addWidget(self.sec_doc, stretch=2)
        lay.addWidget(self.sec_txt, stretch=3)
        return page

    def _apply_filter(self):
        want_obj = self.chip_all.isChecked() or self.chip_obj.isChecked()
        want_doc = self.chip_all.isChecked() or self.chip_doc.isChecked()
        want_txt = self.chip_all.isChecked() or self.chip_txt.isChecked()
        self.sec_obj.setVisible(want_obj and self.t_obj.rowCount() > 0)
        self.sec_doc.setVisible(want_doc and self.t_doc.rowCount() > 0)
        self.sec_txt.setVisible(want_txt and self.t_txt.rowCount() > 0)

    # ---------------------------------------------------------------- results
    def show_empty(self):
        """Back to the initial search state — clears the results view."""
        self.header.setText("Search")
        self.stack.setCurrentIndex(0)

    def show_results(self, query: str, objects, documents, texts,
                     elapsed_ms: float | None = None):
        self.header.setText(f'Search — “{query}”')

        self.t_obj.setSortingEnabled(False)
        self.t_obj.setRowCount(0)
        for i, o in enumerate(objects):
            self.t_obj.insertRow(i)
            self.t_obj.setItem(i, 0, colored_item(
                o["tag"], TYPE_COLORS.get(o["type"], PALETTE["text"]), mono=True))
            self.t_obj.setItem(i, 1, QTableWidgetItem(o["type"]))
            self.t_obj.setItem(i, 2, colored_item(
                "yes" if o["in_model"] else "", PALETTE["success"]))
            self.t_obj.setItem(i, 3, QTableWidgetItem(str(o["hits"])))
        self.t_obj.setSortingEnabled(True)

        self._fill(self.t_doc, [[d["doc_number"] or "", d["revision"] or "",
                                 d["title"] or "", d["name"]] for d in documents],
                   role_col=3, roles=[d["path"] for d in documents])
        self._fill(self.t_txt, [[t["name"], str(t["page"]),
                                 t["snip"].replace("\n", " ")] for t in texts],
                   role_col=0, roles=[t["path"] for t in texts])

        n_obj, n_doc, n_txt = (self.t_obj.rowCount(), self.t_doc.rowCount(),
                               self.t_txt.rowCount())
        total = n_obj + n_doc + n_txt
        self.sec_obj.set_count(n_obj)
        self.sec_doc.set_count(n_doc)
        self.sec_txt.set_count(n_txt)
        self.chip_obj.setText(f"Objects {n_obj}")
        self.chip_doc.setText(f"Documents {n_doc}")
        self.chip_txt.setText(f"Text {n_txt}")
        timing = f"  ·  {elapsed_ms:.0f} ms" if elapsed_ms is not None else ""
        self.summary.setText(
            f"{total} result{'s' if total != 1 else ''} for “{query}”{timing}"
            "  —  double-click a row to open")

        for table in (self.t_obj, self.t_doc, self.t_txt):
            for col in range(table.columnCount() - 1):
                table.resizeColumnToContents(col)

        if total == 0:
            self.no_results.setText(
                f'No matches for "{query}" — if this tag style should exist, '
                "add it on the Patterns page and re-index.")
            self.stack.setCurrentIndex(0)
        else:
            self.no_results.setText("")
            self.chip_all.setChecked(True)
            self._apply_filter()
            self.stack.setCurrentIndex(1)

    @staticmethod
    def _fill(table, rows, role_col=None, roles=None):
        table.setSortingEnabled(False)
        table.setRowCount(0)
        for i, row in enumerate(rows):
            table.insertRow(i)
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                if role_col is not None and j == role_col and roles:
                    item.setData(Qt.UserRole, roles[i])
                table.setItem(i, j, item)
        table.setSortingEnabled(True)

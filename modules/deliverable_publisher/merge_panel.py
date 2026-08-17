"""
Merge view for the Deliverable Publisher module.

Occupies the same workspace the publish cards use — the page swaps between the
two rather than opening a second window.
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QFileDialog,
                               QHBoxLayout, QLabel, QListWidget, QVBoxLayout)

from ui.triz_widgets import TRIZCard, TRIZButton, FormField
from modules.deliverable_publisher.merge import (collect_pdfs,
                                                 normalize_pdf_name)


class MergePanel(TRIZCard):
    merge_requested = Signal()

    def __init__(self):
        super().__init__("Merge PDFs", step=2, color="#38BDF8")

        self.pdf_paths: list[Path] = []
        self.source_folder: Path | None = None

        hint = QLabel("Combine already-published PDFs — no AutoCAD required. "
                      "Order top to bottom.")
        hint.setObjectName("Muted")
        hint.setWordWrap(True)

        # source row -------------------------------------------------
        source_row = QHBoxLayout()
        source_row.setSpacing(10)
        self.browse_btn = TRIZButton("Browse Folder", kind="ghost", width=140)
        self.browse_btn.clicked.connect(self.browse_folder)
        self.recurse_check = QCheckBox("Include subfolders")
        self.recurse_check.stateChanged.connect(lambda _: self.reload())
        self.count_label = QLabel("0 files")
        self.count_label.setObjectName("Muted")
        source_row.addWidget(self.browse_btn)
        source_row.addWidget(self.recurse_check)
        source_row.addStretch()
        source_row.addWidget(self.count_label)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet(
            "color: #6B7280; font-family: Consolas, monospace; font-size: 10px;")

        # list -------------------------------------------------------
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.setStyleSheet(
            "QListWidget { background: #0A101C; border: 1px solid #1E2A40;"
            " border-radius: 6px; font-family: Consolas, monospace;"
            " font-size: 11px; color: #D1D5DB; padding: 4px; }"
            "QListWidget::item { padding: 3px 6px; }"
            "QListWidget::item:selected { background: #1E3A8A; color: #E8EDF6; }")
        self.list_widget.setMinimumHeight(180)

        # reorder buttons --------------------------------------------
        tools = QHBoxLayout()
        tools.setSpacing(8)
        self.up_btn = TRIZButton("Move Up", kind="ghost", width=110)
        self.down_btn = TRIZButton("Move Down", kind="ghost", width=110)
        self.remove_btn = TRIZButton("Remove", kind="ghost", width=110)
        self.reset_btn = TRIZButton("Reset Order", kind="ghost", width=120)
        self.up_btn.clicked.connect(self.move_up)
        self.down_btn.clicked.connect(self.move_down)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.reset_btn.clicked.connect(self.reload)
        for btn in (self.up_btn, self.down_btn, self.remove_btn, self.reset_btn):
            tools.addWidget(btn)
        tools.addStretch()

        # output -----------------------------------------------------
        self.output_name = FormField(
            label="Merged Filename",
            placeholder="Merged.pdf",
        )

        self.archive_check = QCheckBox("Archive source PDFs after merge")

        self.merge_btn = TRIZButton("Merge Selected", kind="success", width=160)
        self.merge_btn.clicked.connect(self.merge_requested.emit)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addWidget(self.archive_check)
        action_row.addStretch()
        action_row.addWidget(self.merge_btn)

        self.status_label = QLabel("Browse to a folder of published PDFs to begin")
        self.status_label.setObjectName("Muted")

        self.layout.setSpacing(10)
        self.layout.addWidget(hint)
        self.layout.addLayout(source_row)
        self.layout.addWidget(self.folder_label)
        self.layout.addWidget(self.list_widget, stretch=1)
        self.layout.addLayout(tools)
        self.layout.addWidget(self.output_name)
        self.layout.addLayout(action_row)
        self.layout.addWidget(self.status_label)

    # ------------------------------------------------------------ loading
    def browse_folder(self):
        start = str(self.source_folder) if self.source_folder else ""
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder containing published PDFs", start)
        if folder:
            self.load_folder(Path(folder))

    def load_folder(self, folder: Path):
        self.source_folder = Path(folder)
        self.folder_label.setText(str(folder))
        self.reload()

    def reload(self):
        if not self.source_folder:
            return
        self.pdf_paths = collect_pdfs(self.source_folder,
                                      self.recurse_check.isChecked())
        self.refresh()
        if self.pdf_paths:
            self.set_status(f"{len(self.pdf_paths)} PDF(s) ready to merge")
        else:
            self.set_status("No PDFs found in that folder", "#F59E0B")

    def refresh(self, keep=None):
        self.list_widget.clear()
        for index, path in enumerate(self.pdf_paths, start=1):
            self.list_widget.addItem(f"{index:>3}.  {path.name}")
        for row in keep or []:
            if 0 <= row < self.list_widget.count():
                self.list_widget.item(row).setSelected(True)
        count = len(self.pdf_paths)
        self.count_label.setText(f"{count} file{'s' if count != 1 else ''}")

    # ------------------------------------------------------------ ordering
    def selected_rows(self):
        return sorted(self.list_widget.row(i)
                      for i in self.list_widget.selectedItems())

    def remove_selected(self):
        rows = self.selected_rows()
        if not rows:
            return
        for row in reversed(rows):
            del self.pdf_paths[row]
        self.refresh()

    def move_up(self):
        rows = self.selected_rows()
        if not rows or rows[0] == 0:
            return
        for row in rows:
            self.pdf_paths[row - 1], self.pdf_paths[row] = (
                self.pdf_paths[row], self.pdf_paths[row - 1])
        self.refresh([r - 1 for r in rows])

    def move_down(self):
        rows = self.selected_rows()
        if not rows or rows[-1] == len(self.pdf_paths) - 1:
            return
        for row in reversed(rows):
            self.pdf_paths[row], self.pdf_paths[row + 1] = (
                self.pdf_paths[row + 1], self.pdf_paths[row])
        self.refresh([r + 1 for r in rows])

    # ------------------------------------------------------------- values
    def values(self):
        return {
            "merge_name": normalize_pdf_name(self.output_name.text().strip()),
            "merge_recurse": self.recurse_check.isChecked(),
            "merge_archive_sources": self.archive_check.isChecked(),
            "merge_folder": str(self.source_folder) if self.source_folder else "",
        }

    def set_values(self, values: dict):
        self.output_name.set_text(values.get("merge_name", "Merged.pdf"))
        self.recurse_check.setChecked(bool(values.get("merge_recurse", False)))
        self.archive_check.setChecked(
            bool(values.get("merge_archive_sources", False)))
        folder = values.get("merge_folder", "")
        if folder and Path(folder).is_dir():
            self.load_folder(Path(folder))

    def set_status(self, text: str, color: str = "#64748B"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def set_merging(self, active: bool):
        self.merge_btn.setEnabled(not active)
        self.browse_btn.setEnabled(not active)

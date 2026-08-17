from pathlib import Path

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QMessageBox,
    QScrollArea,
    QStackedWidget,
)

from core.jobs import Job
from modules.deliverable_publisher.publisher import DeliverablePublisherEngine
from modules.deliverable_publisher.settings import get_settings
from modules.deliverable_publisher.setup_panel import SetupPanel
from modules.deliverable_publisher.scan_panel import ScanPanel
from modules.deliverable_publisher.options_panel import OptionsPanel
from modules.deliverable_publisher.drawing_list_panel import DrawingListPanel
from modules.deliverable_publisher.summary_panel import SummaryPanel
from modules.deliverable_publisher.merge_panel import MergePanel
from modules.deliverable_publisher.merge import (PYMUPDF_AVAILABLE,
                                                 archive_source_pdfs,
                                                 merge_pdfs)
from ui.triz_widgets import TRIZButton
from ui.progress_widget import TRIZProgressWidget
from ui.workflow_stepper import WorkflowStepper


class DeliverablePublisherPage(QWidget):
    def __init__(self, platform=None):
        super().__init__()

        self.platform = platform
        self.settings = get_settings()
        self.engine = DeliverablePublisherEngine(platform)

        self.current_dwgs = []
        self.is_publishing = False
        # Workspace view: "publish" or "merge" — same space, swapped in place.
        self.view_mode = "publish"

        self.build_ui()
        self.connect_signals()
        self.connect_job_signals()
        self.load_settings()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        self.title_label = QLabel("Deliverable Publisher")
        self.title_label.setObjectName("Title")

        self.subtitle_label = QLabel("Batch plot and publish drawing packages.")
        self.subtitle_label.setObjectName("Subtitle")

        self.view_toggle_btn = TRIZButton("Merge PDFs", kind="ghost", width=140)
        self.view_toggle_btn.clicked.connect(self.toggle_view)

        header_row = QHBoxLayout()
        header_col = QVBoxLayout()
        header_col.setSpacing(2)
        header_col.addWidget(self.title_label)
        header_col.addWidget(self.subtitle_label)
        header_row.addLayout(header_col)
        header_row.addStretch()
        header_row.addWidget(self.view_toggle_btn, alignment=Qt.AlignTop)

        layout.addLayout(header_row)

        self.stepper = WorkflowStepper()
        self.setup_panel = SetupPanel()
        self.scan_panel = ScanPanel()
        self.options_panel = OptionsPanel()
        self.summary_panel = SummaryPanel()
        self.drawing_list_panel = DrawingListPanel()
        self.progress_widget = TRIZProgressWidget()
        self.merge_panel = MergePanel()

        # Minimums must clear each card's own sizeHint, or Qt squeezes children
        # past their minimums and they overlap.
        for panel, floor in (
            (self.setup_panel, 270),
            (self.options_panel, 300),
            (self.scan_panel, 210),
            (self.summary_panel, 260),
        ):
            panel.setMinimumHeight(max(floor, panel.sizeHint().height()))

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        grid.addWidget(self.setup_panel, 0, 0)
        grid.addWidget(self.scan_panel, 0, 1)
        grid.addWidget(self.options_panel, 1, 0)
        grid.addWidget(self.summary_panel, 1, 1)

        grid.setColumnStretch(0, 5)
        grid.setColumnStretch(1, 4)
        grid.setRowStretch(0, 5)
        grid.setRowStretch(1, 4)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 4, 0)
        scroll_layout.setSpacing(12)

        scroll_layout.addWidget(self.stepper)
        scroll_layout.addLayout(grid)
        scroll_layout.addWidget(self.progress_widget)
        scroll_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setWidget(scroll_content)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollArea > QWidget > QWidget {
                background: transparent;
            }

            QScrollBar:vertical {
                background: #0A101C;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #1E2A40;
                min-height: 30px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #2B3B58;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            """
        )

        merge_container = QWidget()
        merge_layout = QVBoxLayout(merge_container)
        merge_layout.setContentsMargins(0, 0, 4, 0)
        merge_layout.setSpacing(12)
        merge_layout.addWidget(self.merge_panel, stretch=1)

        self.views = QStackedWidget()
        self.views.addWidget(scroll_area)       # 0 — publish
        self.views.addWidget(merge_container)   # 1 — merge
        layout.addWidget(self.views, stretch=1)

        self.stepper.set_active_step(1)

    def connect_signals(self):
        self.scan_panel.scan_requested.connect(self.scan_dwgs)
        self.scan_panel.clear_requested.connect(self.clear)
        self.options_panel.save_requested.connect(self.save_settings)
        self.options_panel.publish_requested.connect(self.publish)
        self.options_panel.cancel_requested.connect(self.cancel_publish)
        self.merge_panel.merge_requested.connect(self.merge)

    def connect_job_signals(self):
        if self.platform and hasattr(self.platform, "jobs"):
            self.platform.jobs.job_finished.connect(self.on_publish_finished)
            self.platform.jobs.job_failed.connect(self.on_publish_failed)

    def load_settings(self):
        values = {
            "drawing_folder": self.settings.get("drawing_folder", ""),
            "output_folder": self.settings.get("output_folder", ""),
            "page_setup": self.settings.get("page_setup", "Deliverable Publisher"),
            "template_dwg": self.settings.get("template_dwg", ""),
            "recurse": self.settings.get("recurse", True),
            "overwrite_pdfs": self.settings.get("overwrite_pdfs", True),
            "close_drawings_after_publish": self.settings.get("close_drawings_after_publish", True),
            "write_csv_log": self.settings.get("write_csv_log", True),
            "layout_mode": self.settings.get("layout_mode", "model"),
            "layout_filter": self.settings.get("layout_filter", "ISO"),
            "merge_folder": self.settings.get("merge_folder", ""),
            "merge_name": self.settings.get("merge_name", "Merged.pdf"),
            "merge_recurse": self.settings.get("merge_recurse", False),
            "merge_archive_sources": self.settings.get(
                "merge_archive_sources", False),
        }

        self.setup_panel.set_values(values)
        self.scan_panel.set_values(values)
        self.options_panel.set_values(values)
        self.merge_panel.set_values(values)

    def collect_values(self):
        values = {}
        values.update(self.setup_panel.values())
        values.update(self.scan_panel.values())
        values.update(self.options_panel.values())
        values.update(self.merge_panel.values())
        return values

    def save_settings(self):
        self.settings.update(self.collect_values())
        self.engine.write("Deliverable Publisher settings saved.", "SUCCESS")

    def scan_dwgs(self):
        self.save_settings()

        values = self.collect_values()
        self.current_dwgs = self.scan_folder(
            values["drawing_folder"],
            values["recurse"]
        )

        self.drawing_list_panel.set_drawings(self.current_dwgs)
        self.scan_panel.set_scanned(len(self.current_dwgs))
        self.summary_panel.set_drawings(len(self.current_dwgs))
        self.summary_panel.set_status("Scanned")

        self.progress_widget.update_progress(
            0,
            max(len(self.current_dwgs), 1),
            "Ready to Publish",
            "--"
        )

        self.stepper.set_active_step(2)
        self.engine.write(
            f"Loaded {len(self.current_dwgs)} DWGs into publisher list.",
            "INFO"
        )

    def scan_folder(self, folder, recurse):
        path = Path(folder)

        if not folder:
            self.engine.write("No drawing folder selected.", "WARNING")
            return []

        if not path.exists():
            self.engine.write(f"Folder does not exist: {folder}", "ERROR")
            return []

        dwgs = sorted(path.rglob("*.dwg")) if recurse else sorted(path.glob("*.dwg"))

        self.engine.write(f"Scanned folder: {folder}", "INFO")
        self.engine.write(f"Found {len(dwgs)} DWG files.", "SUCCESS")

        return dwgs

    def build_publish_config(self):
        values = self.collect_values()

        return self.engine.build_config(
            drawing_folder=values["drawing_folder"],
            output_folder=values["output_folder"],
            page_setup_name=values["page_setup"],
            recurse=values["recurse"],
            layout_mode=values.get("layout_mode", "model"),
            layout_filter=values.get("layout_filter", ""),
            folder_mode="mirror",
            log_csv=values["write_csv_log"],
            template_dwg=values["template_dwg"] or None,
        )

    def publish(self):
        if self.is_publishing:
            self.engine.write("Publish is already running.", "WARNING")
            return

        self.save_settings()

        self.is_publishing = True
        self.options_panel.set_publishing(True)
        self.scan_panel.set_publishing(True)
        self.summary_panel.set_status("Publishing")
        self.stepper.set_active_step(3)

        self.progress_widget.update_progress(
            0,
            max(len(self.current_dwgs), 1),
            "Publishing",
            "Starting..."
        )

        job = Job(
            name="Deliverable Publisher",
            function=self.engine.publish,
            args=(self.build_publish_config(),)
        )

        self.engine.write("Starting Deliverable Publisher background job.", "JOB")

        if self.platform and hasattr(self.platform, "jobs"):
            self.platform.jobs.submit(job)
        else:
            result = self.engine.publish(self.build_publish_config())
            self.handle_publish_result(result)

    def cancel_publish(self):
        self.engine.write(
            "Cancel requested. Safe cancellation will be connected next.",
            "WARNING"
        )
        self.summary_panel.set_status("Cancel Requested")

    def on_publish_finished(self, job_result):
        if job_result.name == "Deliverable Publisher":
            self.handle_publish_result(job_result.result)

    def on_publish_failed(self, job_result):
        if job_result.name != "Deliverable Publisher":
            return

        self.is_publishing = False
        self.options_panel.set_publishing(False)
        self.scan_panel.set_publishing(False)

        self.summary_panel.set_status("Failed")
        self.progress_widget.update_progress(0, 1, "Failed", "Job failed")

        self.engine.write(
            f"Publishing job failed: {job_result.error}",
            "ERROR"
        )

    def handle_publish_result(self, result):
        self.is_publishing = False
        self.options_panel.set_publishing(False)
        self.scan_panel.set_publishing(False)

        if not isinstance(result, dict):
            self.summary_panel.set_status("Failed")
            self.engine.write("Publishing returned an invalid result.", "ERROR")
            return

        if "error" in result:
            self.summary_panel.set_status("Failed")
            self.progress_widget.update_progress(0, 1, "Failed", result["error"])
            self.engine.write(f"Publishing failed: {result['error']}", "ERROR")
            return

        processed = result.get("processed_dwgs", 0)
        total = result.get("total_dwgs", processed)

        self.summary_panel.apply_result(result)

        self.progress_widget.update_progress(
            processed,
            max(total, 1),
            "Complete",
            "Publishing complete"
        )

        self.stepper.set_active_step(4)
        self.engine.write("Publishing finished successfully.", "SUCCESS")

    # ======================
    # View switching (publish <-> merge)
    # ======================
    def toggle_view(self):
        if self.view_mode == "publish":
            self.show_merge_view()
        else:
            self.show_publish_view()

    def show_merge_view(self):
        self.views.setCurrentIndex(1)
        self.title_label.setText("Deliverable Publisher")
        self.subtitle_label.setText(
            "Combine already-published PDFs into a single file.")
        self.view_toggle_btn.setText("Back to Publish")
        self.view_mode = "merge"

    def show_publish_view(self):
        self.views.setCurrentIndex(0)
        self.title_label.setText("Deliverable Publisher")
        self.subtitle_label.setText("Batch plot and publish drawing packages.")
        self.view_toggle_btn.setText("Merge PDFs")
        self.view_mode = "publish"

    # ======================
    # Merge (phase 2)
    # ======================
    def merge(self):
        if not PYMUPDF_AVAILABLE:
            QMessageBox.warning(
                self, "Merge PDFs",
                "PyMuPDF is not installed.\n\n"
                "Install it with:  pip install PyMuPDF")
            return

        paths = list(self.merge_panel.pdf_paths)
        if not paths:
            self.merge_panel.set_status(
                "Nothing to merge — browse to a folder first", "#F59E0B")
            return

        values = self.merge_panel.values()
        output = self.merge_panel.source_folder / values["merge_name"]

        if any(p.resolve() == output.resolve() for p in paths):
            self.merge_panel.set_status(
                "Merged filename matches a source PDF — rename it", "#EF4444")
            return

        if output.exists():
            confirm = QMessageBox.question(
                self, "Merge PDFs",
                f"{output.name} already exists.\n\nOverwrite it?")
            if confirm != QMessageBox.Yes:
                return

        self.save_settings()
        self.merge_panel.set_merging(True)
        self.merge_panel.set_status(
            f"Merging {len(paths)} PDFs...", "#38BDF8")

        try:
            merge_pdfs(paths, output, self.engine.write)
            if values["merge_archive_sources"]:
                archive_source_pdfs(paths, self.engine.write)
                self.merge_panel.reload()
            self.merge_panel.set_status(
                f"Created {output.name}", "#22C55E")
            self.summary_panel.set_status("Merged")
            if self.platform:
                self.platform.notify(
                    "Deliverable Publisher",
                    f"Merged {len(paths)} PDFs into {output.name}", "success")
        except Exception as e:
            self.merge_panel.set_status(f"Merge failed: {e}", "#EF4444")
            self.engine.write(f"Merge failed: {e}", "ERROR")
            QMessageBox.critical(self, "Merge PDFs", str(e))
        finally:
            self.merge_panel.set_merging(False)

    def clear(self):
        self.current_dwgs.clear()

        self.drawing_list_panel.clear()
        self.scan_panel.reset()
        self.summary_panel.reset()
        self.progress_widget.reset()
        self.stepper.set_active_step(1)

        self.engine.write("Deliverable Publisher cleared.")
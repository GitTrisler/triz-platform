from pathlib import Path

from modules.title_block_manager.settings import get_settings
from modules.title_block_manager.extractor import TitleBlockExtractor
from modules.title_block_manager.setup_panel import SetupPanel
from modules.title_block_manager.scan_panel import ScanPanel
from modules.title_block_manager.options_panel import OptionsPanel
from modules.title_block_manager.summary_panel import SummaryPanel

from ui.module_workspace import ModuleWorkspace


class TitleBlockManagerPage(ModuleWorkspace):
    def __init__(self, platform=None):
        self.platform = platform
        self.settings = get_settings()
        self.extractor = TitleBlockExtractor(platform)
        self.last_extract_result = None

        super().__init__(
            title="Title Block Manager",
            subtitle="Generate and update title block Excel templates.",
            steps=[
                ("Set Up", "Select drawing folder and block settings", "#38BDF8"),
                ("Extract", "Generate Excel template from DWGs", "#22C55E"),
                ("Update", "Write completed Excel values", "#A855F7"),
                ("Complete", "Review results and logs", "#F59E0B"),
            ],
            left_width=5,
            right_width=4,
            scroll=False,
        )

        self.setup_panel = SetupPanel()
        self.scan_panel = ScanPanel()
        self.options_panel = OptionsPanel()
        self.summary_panel = SummaryPanel()

        self.setup_panel.setMinimumHeight(340)
        self.scan_panel.setMinimumHeight(205)
        self.options_panel.setMinimumHeight(215)
        self.summary_panel.setMinimumHeight(350)

        self.add_left(self.setup_panel)
        self.add_left(self.options_panel)
        self.add_left_stretch()

        self.add_right(self.scan_panel)
        self.add_right(self.summary_panel)
        self.add_right_stretch()

        self.connect_signals()
        self.load_settings()
        self.set_active_step(1)

    def connect_signals(self):
        self.scan_panel.extract_requested.connect(self.extract_template)
        self.scan_panel.clear_requested.connect(self.clear_scan)

        self.options_panel.save_requested.connect(self.save_settings)
        self.options_panel.run_requested.connect(self.run_update_placeholder)
        self.options_panel.cancel_requested.connect(self.cancel_update_placeholder)
        self.options_panel.reset_requested.connect(self.reset_all)

    def load_settings(self):
        values = {
            "excel_file": self.settings.get("excel_file", ""),
            "drawing_folder": self.settings.get("drawing_folder", ""),
            "output_folder": self.settings.get("output_folder", ""),
            "worksheet": self.settings.get("worksheet", ""),
            "key_column": self.settings.get("key_column", "CADFILE"),
            "block_name": self.settings.get("block_name", "TITLEBLOCK"),
            "dry_run": self.settings.get("dry_run", True),
            "replace_fields": self.settings.get("replace_fields", False),
            "write_blank_values": self.settings.get("write_blank_values", False),
            "include_subfolders": self.settings.get("include_subfolders", True),
        }

        self.setup_panel.set_values(values)
        self.options_panel.set_values(values)

    def collect_values(self):
        values = {}
        values.update(self.setup_panel.values())
        values.update(self.options_panel.values())
        return values

    def save_settings(self):
        self.settings.update(self.collect_values())

        if self.platform:
            self.platform.output_write(
                "Title Block Manager settings saved.",
                "SUCCESS",
            )

    def extract_template(self):
        self.save_settings()

        values = self.collect_values()

        self.last_extract_result = None
        self.summary_panel.set_status("Extracting")
        self.update_progress(0, 1, "Extracting Template", "Opening AutoCAD...")
        self.set_active_step(2)

        result = self.extractor.extract_template(values)

        if "error" in result:
            self.scan_panel.reset()
            self.summary_panel.set_status("Failed")
            self.update_progress(0, 1, "Extraction Failed", result["error"])

            if self.platform:
                self.platform.output_write(result["error"], "ERROR")

            return

        self.last_extract_result = result

        drawings = result.get("drawings", 0)
        attributes = result.get("attributes", 0)
        rows = result.get("rows", 0)
        failed = result.get("failed", 0)
        template_path = result.get("template_path", "")

        self.scan_panel.set_results(
            drawings=drawings,
            attributes=attributes,
            rows=rows,
            status="Template generated successfully.",
        )

        self.summary_panel.set_drawings(drawings)
        self.summary_panel.set_rows(rows)
        self.summary_panel.set_matched(drawings - failed)
        self.summary_panel.set_updated(0)
        self.summary_panel.set_failed(failed)
        self.summary_panel.set_status("Template")

        self.update_progress(
            rows,
            max(rows, 1),
            "Template Generated",
            template_path,
        )

        if self.platform:
            self.platform.output_write(
                f"Generated title block template: {template_path}",
                "SUCCESS",
            )

    def clear_scan(self):
        self.last_extract_result = None
        self.scan_panel.reset()

        self.summary_panel.set_rows(0)
        self.summary_panel.set_drawings(0)
        self.summary_panel.set_matched(0)
        self.summary_panel.set_updated(0)
        self.summary_panel.set_failed(0)
        self.summary_panel.set_status("Ready")

        self.reset_progress()
        self.set_active_step(1)

        if self.platform:
            self.platform.output_write(
                "Title Block Manager extraction cleared.",
                "INFO",
            )

    def reset_all(self):
        self.last_extract_result = None
        self.scan_panel.reset()
        self.summary_panel.reset()
        self.reset_progress()
        self.set_active_step(1)

        if self.platform:
            self.platform.output_write(
                "Title Block Manager reset.",
                "INFO",
            )

    def run_update_placeholder(self):
        values = self.collect_values()
        excel_file = values.get("excel_file", "").strip()

        if not excel_file:
            if self.platform:
                self.platform.output_write(
                    "Select a completed Excel file before running update.",
                    "WARNING",
                )
            return

        if not Path(excel_file).exists():
            if self.platform:
                self.platform.output_write(
                    f"Completed Excel file not found: {excel_file}",
                    "ERROR",
                )
            return

        dry_run = self.options_panel.values().get("dry_run")

        self.summary_panel.set_status("Dry Run" if dry_run else "Ready")
        self.set_active_step(3)

        self.update_progress(
            0,
            1,
            "Update engine not wired yet",
            "Next step: completed Excel update engine",
        )

        if self.platform:
            self.platform.output_write(
                "Completed Excel file found. Update engine is not wired yet.",
                "WARNING",
            )

    def cancel_update_placeholder(self):
        if self.platform:
            self.platform.output_write(
                "Cancel is not active yet because the update engine is not wired.",
                "WARNING",
            )
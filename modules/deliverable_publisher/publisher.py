from pathlib import Path
import traceback

from modules.deliverable_publisher.acad import AutoCADSession, PYWIN32_AVAILABLE
from modules.deliverable_publisher.csv_logger import CSVLogger
from modules.deliverable_publisher.models import PublishConfig
from modules.deliverable_publisher.utils import (
    ACC_TEMP_ROOT,
    create_working_copy,
    cleanup_temp_file,
    select_layouts,
    generate_pdf_path,
)


class DeliverablePublisherEngine:
    def __init__(self, platform=None):
        self.platform = platform

    def write(self, message, level="INFO"):
        if self.platform:
            self.platform.output_write(message, level)
        else:
            print(f"{level}: {message}")

    def scan_dwgs(self, folder):
        path = Path(folder)

        if not folder:
            self.write("No drawing folder selected.", "WARNING")
            return []

        if not path.exists():
            self.write(f"Folder does not exist: {folder}", "ERROR")
            return []

        if not path.is_dir():
            self.write(f"Path is not a folder: {folder}", "ERROR")
            return []

        dwgs = sorted(path.glob("*.dwg"))

        self.write(f"Scanned folder: {folder}", "INFO")
        self.write(f"Found {len(dwgs)} DWG files.", "SUCCESS")

        return dwgs

    def build_config(
        self,
        drawing_folder,
        output_folder,
        page_setup_name,
        recurse=True,
        layout_mode="model",
        layout_filter="",
        folder_mode="mirror",
        log_csv=True,
        template_dwg=None,
    ):
        return PublishConfig(
            selection_mode="folder",
            input_root=Path(drawing_folder),
            output_root=Path(output_folder),
            page_setup_name=page_setup_name,
            recurse=recurse,
            layout_mode=layout_mode,
            layout_filter=layout_filter,
            folder_mode=folder_mode,
            log_csv=log_csv,
            template_dwg=Path(template_dwg) if template_dwg else None,
        )

    def publish(self, config: PublishConfig):
        if not PYWIN32_AVAILABLE:
            self.write("pywin32 is not installed. Cannot communicate with AutoCAD.", "ERROR")
            return {"error": "pywin32 not available"}

        errors = config.validate()

        if errors:
            message = "Configuration errors:\n" + "\n".join(f"  • {e}" for e in errors)
            self.write(message, "ERROR")
            return {"error": message}

        try:
            if config.selection_mode == "files":
                dwg_files = list(config.dwg_files)
            elif config.recurse:
                dwg_files = list(config.input_root.rglob("*.dwg"))
            else:
                dwg_files = list(config.input_root.glob("*.dwg"))

        except Exception as e:
            message = f"Failed to scan DWG files: {e}"
            self.write(message, "ERROR")
            return {"error": message}

        if not dwg_files:
            self.write("No DWG files found to process.", "WARNING")
            return {"error": "No DWG files to process"}

        self.write("=" * 60, "INFO")
        self.write("Deliverable Publisher started", "JOB")
        self.write(f"Found {len(dwg_files)} DWG file(s) to process", "INFO")
        self.write(f"Page setup: {config.page_setup_name}", "INFO")
        self.write(f"Output folder: {config.output_root}", "INFO")
        self.write(f"ACC temp folder: {ACC_TEMP_ROOT}", "INFO")
        self.write("=" * 60, "INFO")

        acad = AutoCADSession(self.write)

        try:
            acad.start()
            self.write("[OK] AutoCAD session started", "SUCCESS")
        except Exception as e:
            message = f"Failed to connect to AutoCAD: {e}"
            self.write(message, "ERROR")
            return {"error": message}

        csv_log = CSVLogger(config.output_root, config.log_csv)

        stats = {
            "total_dwgs": len(dwg_files),
            "processed_dwgs": 0,
            "failed_dwgs": 0,
            "layouts_plotted": 0,
            "layouts_failed": 0,
            "errors": [],
        }

        for index, dwg_path in enumerate(dwg_files, start=1):
            self.write("", "INFO")
            self.write("-" * 60, "INFO")
            self.write(f"[{index}/{stats['total_dwgs']}] {dwg_path.name}", "JOB")
            self.write("-" * 60, "INFO")

            doc = None
            working_path = None
            is_temp = False

            try:
                working_path, is_temp = create_working_copy(
                    dwg_path,
                    ACC_TEMP_ROOT,
                    self.write
                )

                doc = acad.open_document(str(working_path))
                self.write(f"  [OK] Opened DWG: {working_path.name}", "SUCCESS")

                page_setups = acad.get_page_setup_names(doc)

                if config.page_setup_name not in page_setups:
                    if config.template_dwg and config.template_dwg.exists():
                        self.write(
                            "  [WARN] Page setup not found. Importing from template...",
                            "WARNING"
                        )
                        acad.import_page_setup(
                            doc,
                            str(config.template_dwg),
                            config.page_setup_name
                        )
                        page_setups = acad.get_page_setup_names(doc)

                if page_setups:
                    preview = ", ".join(page_setups[:5])
                    self.write(f"  Page setups: {preview}", "INFO")

                    if len(page_setups) > 5:
                        self.write(
                            f"    ... and {len(page_setups) - 5} more",
                            "INFO"
                        )
                else:
                    self.write("  [WARN] No page setups found in DWG", "WARNING")

                all_layouts = acad.get_layout_names(doc)
                self.write(f"  Layouts: {', '.join(all_layouts)}", "INFO")

                selected_layouts = select_layouts(
                    all_layouts,
                    config.layout_mode,
                    config.layout_filter
                )

                if not selected_layouts:
                    self.write(
                        "  [WARN] No layouts matched selection criteria",
                        "WARNING"
                    )
                    csv_log.log(dwg_path, "", None, "SKIPPED", "No matching layouts")
                    continue

                self.write(
                    f"  Selected layouts: {', '.join(selected_layouts)}",
                    "INFO"
                )

                for layout_name in selected_layouts:
                    self.write("", "INFO")
                    self.write(f"  → Layout: {layout_name}", "JOB")

                    pdf_path = generate_pdf_path(
                        dwg_path,
                        layout_name,
                        config
                    )

                    try:
                        acad.apply_page_setup(
                            doc,
                            layout_name,
                            config.page_setup_name
                        )
                        self.write(
                            f"  [OK] Applied page setup to layout: {layout_name}",
                            "SUCCESS"
                        )

                        acad.plot_to_pdf(
                            doc,
                            str(pdf_path)
                        )

                        stats["layouts_plotted"] += 1
                        self.write(
                            f"  [OK] Plotted PDF: {pdf_path.name}",
                            "SUCCESS"
                        )
                        csv_log.log(dwg_path, layout_name, pdf_path, "SUCCESS", "")

                    except Exception as e:
                        stats["layouts_failed"] += 1
                        error_message = str(e)

                        self.write(
                            f"  [ERROR] Layout failed: {error_message}",
                            "ERROR"
                        )
                        csv_log.log(
                            dwg_path,
                            layout_name,
                            pdf_path,
                            "FAILED",
                            error_message
                        )

                stats["processed_dwgs"] += 1
                self.write(f"  [OK] Finished DWG: {dwg_path.name}", "SUCCESS")

            except Exception as e:
                stats["failed_dwgs"] += 1
                error_message = str(e)
                stats["errors"].append(f"{dwg_path.name}: {error_message}")

                self.write(f"[ERROR] DWG failed: {error_message}", "ERROR")
                self.write(traceback.format_exc(), "ERROR")
                csv_log.log(dwg_path, "", None, "FAILED", error_message)

            finally:
                if doc:
                    try:
                        acad.close_document(doc, save_changes=False)
                        self.write("  [OK] Closed DWG", "SUCCESS")
                    except Exception as e:
                        self.write(
                            f"  [WARN] Failed to close DWG cleanly: {e}",
                            "WARNING"
                        )

                if is_temp and working_path:
                    cleanup_temp_file(working_path, self.write)

        csv_log.close()
        acad.cleanup()

        self.write("", "INFO")
        self.write("=" * 60, "INFO")
        self.write("PUBLISHING COMPLETE", "SUCCESS")
        self.write("=" * 60, "INFO")
        self.write(f"DWGs processed: {stats['processed_dwgs']}/{stats['total_dwgs']}", "INFO")
        self.write(f"DWGs failed: {stats['failed_dwgs']}", "WARNING" if stats["failed_dwgs"] else "INFO")
        self.write(f"Layouts plotted: {stats['layouts_plotted']}", "SUCCESS" if stats["layouts_plotted"] else "INFO")
        self.write(f"Layouts failed: {stats['layouts_failed']}", "WARNING" if stats["layouts_failed"] else "INFO")

        if config.log_csv:
            self.write(f"CSV log: {config.output_root / 'publish_log.csv'}", "INFO")

        if stats["errors"]:
            self.write(f"Errors encountered: {len(stats['errors'])}", "WARNING")

        return stats
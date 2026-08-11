from pathlib import Path
from typing import Optional, List


class PublishConfig:
    """
    Configuration for a Deliverable Publisher run.

    Supports:
    - folder mode: scan an input folder for DWGs
    - files mode: process an explicit list of DWG files
    """

    def __init__(
        self,
        output_root: Path,
        page_setup_name: str,
        selection_mode: str = "folder",
        input_root: Optional[Path] = None,
        dwg_files: Optional[List[Path]] = None,
        recurse: bool = True,
        layout_mode: str = "model",
        layout_filter: str = "",
        folder_mode: str = "mirror",
        log_csv: bool = True,
        template_dwg: Optional[Path] = None,
    ):
        self.selection_mode = selection_mode
        self.input_root = input_root
        self.dwg_files = dwg_files or []
        self.output_root = output_root
        self.page_setup_name = page_setup_name
        self.recurse = recurse
        self.layout_mode = layout_mode
        self.layout_filter = layout_filter
        self.folder_mode = folder_mode
        self.log_csv = log_csv
        self.template_dwg = template_dwg

    def validate(self) -> list[str]:
        errors = []

        if self.selection_mode == "folder":
            if not self.input_root:
                errors.append("Input folder is required for folder mode")
            elif not self.input_root.exists():
                errors.append(f"Input folder does not exist: {self.input_root}")
            elif not self.input_root.is_dir():
                errors.append(f"Input path is not a directory: {self.input_root}")

        elif self.selection_mode == "files":
            if not self.dwg_files:
                errors.append("No DWG files selected")
            else:
                for file_path in self.dwg_files:
                    if not file_path.exists():
                        errors.append(f"File does not exist: {file_path}")

        else:
            errors.append(f"Unknown selection mode: {self.selection_mode}")

        if self.template_dwg and not self.template_dwg.exists():
            errors.append(f"Template DWG does not exist: {self.template_dwg}")

        if not self.page_setup_name:
            errors.append("Page setup name is required")

        if self.layout_mode == "filter" and not self.layout_filter:
            errors.append("Layout filter text is required when filter mode is selected")

        return errors
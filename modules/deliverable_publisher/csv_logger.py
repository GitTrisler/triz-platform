import csv
from datetime import datetime
from pathlib import Path
from typing import Optional


class CSVLogger:
    def __init__(self, output_root: Path, enabled: bool = True):
        self.enabled = enabled
        self.csv_path = output_root / "publish_log.csv" if enabled else None
        self.csv_file = None
        self.csv_writer = None

        if self.enabled:
            self._open()

    def _open(self) -> None:
        try:
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)

            is_new = not self.csv_path.exists()

            self.csv_file = open(
                self.csv_path,
                "a",
                newline="",
                encoding="utf-8"
            )

            self.csv_writer = csv.writer(self.csv_file)

            if is_new:
                self.csv_writer.writerow([
                    "timestamp",
                    "dwg_path",
                    "layout",
                    "pdf_path",
                    "result",
                    "message"
                ])
                self.csv_file.flush()

        except Exception:
            self.enabled = False

    def log(
        self,
        dwg_path: Path,
        layout: str,
        pdf_path: Optional[Path],
        result: str,
        message: str = ""
    ) -> None:
        if not self.enabled or not self.csv_writer:
            return

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.csv_writer.writerow([
                timestamp,
                str(dwg_path),
                layout,
                str(pdf_path) if pdf_path else "",
                result,
                message
            ])

            self.csv_file.flush()

        except Exception:
            pass

    def close(self) -> None:
        if self.csv_file:
            try:
                self.csv_file.close()
            except Exception:
                pass
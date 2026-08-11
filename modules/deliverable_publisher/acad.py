import os
import time
import traceback
from pathlib import Path

from core.logger import log


try:
    import win32com.client
    import pythoncom
    PYWIN32_AVAILABLE = True
except ImportError:
    win32com = None
    pythoncom = None
    PYWIN32_AVAILABLE = False


COM_RETRY_ATTEMPTS = 3
COM_RETRY_DELAY = 0.5
DOCUMENT_READY_TIMEOUT = 15.0
DOCUMENT_READY_POLL = 0.25


def safe_com_call(func, *args, max_retries=COM_RETRY_ATTEMPTS, delay=COM_RETRY_DELAY, **kwargs):
    last_error = None

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)

        except Exception as e:
            last_error = e

            if attempt < max_retries - 1:
                log(f"COM call failed attempt {attempt + 1}/{max_retries}: {e}")
                time.sleep(delay)
            else:
                log(f"COM call failed after {max_retries} attempts: {e}")

    raise RuntimeError(f"COM operation failed after {max_retries} attempts: {last_error}")


class AutoCADSession:
    def __init__(self, ui_logger):
        self.ui_logger = ui_logger
        self.app = None
        self.com_initialized = False

    def write(self, message):
        log(message)
        self.ui_logger(message)

    def start(self):
        self.write("[CONNECT] Connecting to AutoCAD...")

        if not PYWIN32_AVAILABLE:
            raise RuntimeError("pywin32 is not installed.")

        try:
            pythoncom.CoInitialize()
            self.com_initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize COM: {e}")

        try:
            self.app = win32com.client.Dispatch("AutoCAD.Application")
            self.app.Visible = True
            version = getattr(self.app, "Version", "Unknown")
            self.write(f"[OK] Connected to AutoCAD (Version: {version})")

        except Exception as e:
            raise RuntimeError(f"Failed to connect to AutoCAD. Is AutoCAD running? Error: {e}")

    def open_document(self, dwg_path: str):
        self.write(f"[OPEN] Opening: {Path(dwg_path).name}")

        if not os.path.exists(dwg_path):
            raise RuntimeError(f"DWG file not found: {dwg_path}")

        def _open():
            return self.app.Documents.Open(dwg_path, False)

        try:
            doc = safe_com_call(_open)
            self._wait_for_ready(doc)
            return doc

        except Exception as e:
            raise RuntimeError(f"Failed to open DWG: {e}")

    def _wait_for_ready(self, doc):
        start_time = time.time()

        while True:
            try:
                _ = doc.Name
                _ = doc.ActiveLayout.Name
                _ = doc.Layouts.Count
                self.write(f"  [OK] Document ready: {doc.Name}")
                return

            except Exception:
                elapsed = time.time() - start_time

                if elapsed > DOCUMENT_READY_TIMEOUT:
                    raise RuntimeError(
                        f"Timeout waiting for document to be ready "
                        f"(>{DOCUMENT_READY_TIMEOUT}s)"
                    )

                time.sleep(DOCUMENT_READY_POLL)

    def close_document(self, doc, save_changes: bool = False):
        if not doc:
            return

        try:
            doc_name = doc.Name
            doc.Close(save_changes)
            self.write(f"  [OK] Closed: {doc_name}")

        except Exception as e:
            self.write(f"  [WARN] Failed to close document: {e}")

    def get_layout_names(self, doc):
        def _get_layouts():
            layouts = []
            for layout in doc.Layouts:
                layouts.append(layout.Name)
            return layouts

        try:
            return safe_com_call(_get_layouts, max_retries=5, delay=1.0)

        except Exception as e:
            raise RuntimeError(f"Failed to get layout names: {e}")

    def get_page_setup_names(self, doc):
        def _get_setups():
            setups = []
            for pc in doc.PlotConfigurations:
                setups.append(pc.Name)
            return setups

        try:
            return safe_com_call(_get_setups, max_retries=5, delay=1.0)

        except Exception as e:
            self.write(f"  [WARN] Failed to get page setup names: {e}")
            return []

    def import_page_setup(self, target_doc, source_dwg_path: str, page_setup_name: str) -> bool:
        try:
            if not os.path.exists(source_dwg_path):
                self.write(f"  [WARN] Template DWG not found: {source_dwg_path}")
                return False

            self.write(f"  Importing from template: {Path(source_dwg_path).name}")

            self.app.ActiveDocument = target_doc

            try:
                target_doc.SetVariable("FILEDIA", 0)
                target_doc.SetVariable("CMDECHO", 0)
            except Exception:
                pass

            source_path = str(source_dwg_path).replace("\\", "/")
            command = f"-PSETUPIN\n{source_path}\n{page_setup_name}\n"

            target_doc.SendCommand(command)
            time.sleep(2.0)

            try:
                target_doc.SetVariable("FILEDIA", 1)
            except Exception:
                pass

            for pc in target_doc.PlotConfigurations:
                if pc.Name == page_setup_name:
                    self.write(f"  [OK] Imported page setup '{page_setup_name}'")
                    return True

            self.write(f"  [WARN] Page setup '{page_setup_name}' not found after import")
            return False

        except Exception as e:
            self.write(f"  [WARN] Failed to import page setup: {e}")
            log(f"Page setup import error: {traceback.format_exc()}")
            return False

    def apply_page_setup(self, doc, layout_name: str, page_setup_name: str):
        target_layout = None

        for layout in doc.Layouts:
            if layout.Name.lower() == layout_name.lower():
                target_layout = layout
                break

        if target_layout is None:
            raise RuntimeError(f"Layout '{layout_name}' not found in document")

        page_setup = None

        try:
            for pc in doc.PlotConfigurations:
                if pc.Name == page_setup_name:
                    page_setup = pc
                    break

            if page_setup is None:
                raise RuntimeError(f"Page setup '{page_setup_name}' not found in document")

        except Exception as e:
            raise RuntimeError(f"Error accessing page setup '{page_setup_name}': {e}")

        try:
            target_layout.CopyFrom(page_setup)
        except Exception as e:
            raise RuntimeError(f"Failed to apply page setup to layout: {e}")

        try:
            doc.ActiveLayout = target_layout
        except Exception as e:
            raise RuntimeError(f"Failed to activate layout: {e}")

        try:
            current_style = target_layout.StyleSheet
            self.write(f"  [OK] Applied '{page_setup_name}' → '{layout_name}'")

            if current_style:
                self.write(f"    Plot style: {current_style}")
            else:
                self.write("    [WARN] No plot style assigned")

        except Exception:
            self.write(f"  [OK] Applied '{page_setup_name}' → '{layout_name}'")

    def plot_to_pdf(self, doc, output_path: str):
        try:
            doc.SetVariable("BACKGROUNDPLOT", 0)
            doc.SetVariable("CMDECHO", 0)
            doc.SetVariable("EXPERT", 5)

        except Exception as e:
            self.write(f"  [WARN] Failed to set system variables: {e}")

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create output directory: {e}")

        output_file = Path(output_path)

        if output_file.exists():
            try:
                output_file.unlink()
                self.write("  [OK] Deleted existing PDF")
            except Exception:
                self.write("  [WARN] Existing PDF may be locked - attempting overwrite")

        self.write(f"  [PLOT] Plotting: {output_file.name}")

        def _plot():
            doc.Plot.PlotToFile(output_path)

        try:
            safe_com_call(_plot)

            if output_file.exists():
                size_kb = output_file.stat().st_size / 1024
                self.write(f"  [OK] PDF created ({size_kb:.1f} KB)")
            else:
                raise RuntimeError("PDF file was not created")

        except Exception as e:
            error_text = str(e).lower()

            if any(word in error_text for word in ["file", "open", "lock", "access"]):
                raise RuntimeError(
                    f"Cannot write PDF - file may be locked. "
                    f"Close '{output_file.name}' and try again."
                )

            raise RuntimeError(f"Plot failed: {e}")

        finally:
            try:
                doc.SetVariable("EXPERT", 0)
            except Exception:
                pass

    def cleanup(self):
        try:
            if self.app:
                self.app = None

            if self.com_initialized:
                pythoncom.CoUninitialize()
                self.com_initialized = False

        except Exception as e:
            self.write(f"  [WARN] Error during COM cleanup: {e}")
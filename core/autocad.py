import time
from dataclasses import dataclass
from typing import Optional, Any

from core.logger import log


try:
    import win32com.client
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None


@dataclass
class AutoCADState:
    available: bool = False
    running: bool = False
    connected: bool = False
    product: str = "Unknown"
    document: str = ""
    error: str = ""


class AutoCADService:
    def __init__(self):
        self.app: Optional[Any] = None
        self.state = AutoCADState()

    def is_available(self) -> bool:
        return win32com is not None and pythoncom is not None

    def connect(self, visible: bool = True) -> bool:
        self.state.available = self.is_available()

        if not self.state.available:
            self.state.error = "pywin32 is not installed."
            log("AutoCAD connect failed: pywin32 not installed.")
            return False

        try:
            pythoncom.CoInitialize()

            try:
                self.app = win32com.client.GetActiveObject("AutoCAD.Application")
                self.state.running = True
                log("Connected to existing AutoCAD session.")
            except Exception:
                self.app = win32com.client.Dispatch("AutoCAD.Application")
                self.state.running = True
                log("Started new AutoCAD session.")

            self.app.Visible = visible
            self.state.connected = True
            self.state.product = str(getattr(self.app, "Name", "AutoCAD"))

            doc = self.active_document()
            self.state.document = doc.Name if doc else ""

            return True

        except Exception as e:
            self.state.connected = False
            self.state.error = str(e)
            log(f"AutoCAD connect failed: {e}")
            return False

    def disconnect(self):
        self.app = None
        self.state.connected = False
        log("AutoCAD service disconnected.")

    def is_connected(self) -> bool:
        return self.app is not None and self.state.connected

    def active_document(self):
        if not self.is_connected():
            return None

        try:
            return self.app.ActiveDocument
        except Exception as e:
            self.state.error = str(e)
            log(f"Could not get active AutoCAD document: {e}")
            return None

    def active_document_name(self) -> str:
        doc = self.active_document()
        return doc.Name if doc else ""

    def active_layout_name(self) -> str:
        doc = self.active_document()
        if not doc:
            return ""

        try:
            return doc.ActiveLayout.Name
        except Exception as e:
            log(f"Could not get active layout: {e}")
            return ""

    def send_command(self, command: str, delay: float = 0.25) -> bool:
        doc = self.active_document()
        if not doc:
            log("SendCommand failed: no active document.")
            return False

        try:
            if not command.endswith("\n"):
                command += "\n"

            doc.SendCommand(command)
            time.sleep(delay)
            log(f"AutoCAD command sent: {command.strip()}")
            return True

        except Exception as e:
            log(f"SendCommand failed: {e}")
            return False

    def save(self) -> bool:
        doc = self.active_document()
        if not doc:
            log("Save failed: no active document.")
            return False

        try:
            doc.Save()
            log(f"Saved drawing: {doc.Name}")
            return True
        except Exception as e:
            log(f"Save failed: {e}")
            return False

    def close_active_document(self, save_changes: bool = False) -> bool:
        doc = self.active_document()
        if not doc:
            log("Close failed: no active document.")
            return False

        try:
            name = doc.Name
            doc.Close(save_changes)
            log(f"Closed drawing: {name}")
            return True
        except Exception as e:
            log(f"Close failed: {e}")
            return False

    def wait_until_quiet(self, timeout: int = 60) -> bool:
        if not self.is_connected():
            return False

        start = time.time()

        while time.time() - start < timeout:
            try:
                if not self.app.GetAcadState().IsQuiescent:
                    time.sleep(0.25)
                    continue

                return True

            except Exception:
                time.sleep(0.25)

        log("AutoCAD wait_until_quiet timed out.")
        return False

    def get_state(self) -> AutoCADState:
        if not self.is_available():
            self.state.available = False
            self.state.error = "pywin32 is not installed."
            return self.state

        self.state.available = True
        self.state.connected = self.is_connected()

        if self.is_connected():
            try:
                self.state.product = str(getattr(self.app, "Name", "AutoCAD"))
                self.state.document = self.active_document_name()
            except Exception as e:
                self.state.error = str(e)

        return self.state


acad = AutoCADService()

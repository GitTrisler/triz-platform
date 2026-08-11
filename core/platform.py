from core.autocad import acad
from core.jobs import job_manager
from core.notifications import notification_center
from core.settings import load_config, save_config
from core.logger import log


class PlatformAPI:
    def __init__(self, app=None):
        self.app = app
        self.autocad = acad
        self.jobs = job_manager
        self.notifications = notification_center
        self.settings = load_config()

    def log(self, message: str):
        log(message)

    def notify(self, title: str, message: str, level: str = "info"):
        note = self.notifications.add(title, message, level)
        log(f"Notification [{level}] {title}: {message}")
        return note

    def save_settings(self):
        save_config(self.settings)
        log("Platform settings saved.")

    def open_module(self, module_name: str):
        if self.app and hasattr(self.app, "open_page"):
            self.app.open_page(module_name)

    def output_write(self, message: str, level: str = "INFO"):
        if self.app and hasattr(self.app, "output"):
            self.app.output.write(message, level)
        else:
            log(f"[{level}] {message}")

    def job_write(self, message: str):
        if self.app and hasattr(self.app, "output"):
            self.app.output.write_job(message)
        else:
            log(message)

    def notification_write(self, message: str):
        if self.app and hasattr(self.app, "output"):
            self.app.output.notify(message)
        else:
            log(message)
"""
Project Hub — platform module page.

Wraps the Hub's HubShell (the same widget its standalone window hosts) so the
engine has exactly one implementation. This adapter's only jobs are:

  · persist the last-opened project through ModuleSettings, not QSettings, so
    it lands in the platform's settings/ folder like every other module
  · keep the Hub's stylesheet scoped to itself — the Hub's "Drafting" design
    system and the platform STYLE both claim #Card / #Sidebar / #Title, and a
    widget-level sheet wins over the app-level one for that subtree
  · leave Ctrl+K to the platform command palette (the Hub falls back to Ctrl+F)
"""

from PySide6.QtWidgets import QVBoxLayout, QWidget

from core.module_settings import ModuleSettings

from modules.project_hub.triz_hub.ui.app import HubShell


class _SettingsShim:
    """QSettings-shaped facade over ModuleSettings so HubShell needs no change."""

    def __init__(self, module_id: str = "project_hub"):
        self._settings = ModuleSettings(module_id, defaults={"last_project": ""})

    def value(self, key, default=None):
        return self._settings.get(key, default)

    def setValue(self, key, value):
        self._settings.set(key, value)


class ProjectHubPage(QWidget):
    def __init__(self, platform=None, parent=None):
        super().__init__(parent)
        self.platform = platform

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.shell = HubShell(platform=platform, settings=_SettingsShim())
        layout.addWidget(self.shell)

    # -- convenience passthroughs for the platform / command palette --------
    def open_project(self, root: str):
        self.shell.open_project(root)

    def start_index(self):
        self.shell.start_index()

    def show_object(self, tag: str):
        self.shell.show_object(tag)

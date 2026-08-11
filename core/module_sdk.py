from dataclasses import dataclass


@dataclass
class ModuleInfo:
    id: str
    name: str
    category: str = "General"
    version: str = "1.0.0"
    author: str = "Trisler Automation"
    description: str = ""
    accent: str = "#38BDF8"


class TRIZModule:
    """
    Base class for all TRIZ Platform modules.
    Every module should inherit from this.
    """

    def __init__(self, platform=None):
        self.platform = platform

    def info(self) -> ModuleInfo:
        raise NotImplementedError("Module must return ModuleInfo.")

    def create_page(self):
        raise NotImplementedError("Module must implement create_page().")

    def on_load(self):
        pass

    def on_open(self):
        pass

    def on_close(self):
        pass

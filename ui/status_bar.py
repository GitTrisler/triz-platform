from PySide6.QtWidgets import QStatusBar


class TRIZStatusBar(QStatusBar):

    def __init__(self):

        super().__init__()

        self.python_version = "3.13"

        self.module = "Dashboard"

        self.autocad = "Not Connected"

        self.refresh()

    def set_module(self, module):

        self.module = module

        self.refresh()

    def set_autocad(self, state):

        self.autocad = state

        self.refresh()

    def refresh(self):

        self.showMessage(

            f"Ready | "

            f"Python {self.python_version} | "

            f"{self.module} | "

            f"AutoCAD: {self.autocad}"

        )

from pathlib import Path

import win32com.client

from .retry import (
    retry_busy_call,
    wait_until_quiet,
    clear_autocad_state,
)


class AutoCADSession:
    """
    Shared AutoCAD session used by all TRIZ modules.

    Deliverable Publisher
    Title Block Manager
    Smart Tags
    Future modules
    """

    def __init__(self):
        self.app = None

    @property
    def connected(self):
        return self.app is not None

    def start(self, visible=True):
        if self.app:
            return self.app

        self.app = retry_busy_call(
            win32com.client.Dispatch,
            "AutoCAD.Application",
        )

        self.app.Visible = visible

        wait_until_quiet(self.app)

        return self.app

    def stop(self):
        if self.app is None:
            return

        try:
            clear_autocad_state(self.app)
        finally:
            self.app = None

    def active_document(self):
        if self.app is None:
            return None

        try:
            return retry_busy_call(
                lambda: self.app.ActiveDocument
            )
        except Exception:
            return None

    def open(self, filename):
        if self.app is None:
            self.start()

        doc = retry_busy_call(
            self.app.Documents.Open,
            str(filename),
        )

        wait_until_quiet(self.app)

        return doc

    def close(self, document, save=False):
        if document is None:
            return

        retry_busy_call(
            document.Close,
            save,
        )

        wait_until_quiet(self.app)

    def save(self, document):
        retry_busy_call(document.Save)

    def save_as(self, document, filename):
        retry_busy_call(
            document.SaveAs,
            str(filename),
        )

    def documents(self):
        if self.app is None:
            return []

        docs = self.app.Documents

        return [
            docs.Item(i)
            for i in range(docs.Count)
        ]

    def close_all(self):
        if self.app is None:
            return

        clear_autocad_state(self.app)

    def is_running(self):
        return self.app is not None
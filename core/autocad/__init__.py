from .session import AutoCADSession

from .retry import (
    init_com_for_thread,
    uninit_com_for_thread,
    retry_busy_call,
    wait_until_quiet,
    get_attr_retry,
    call_method_retry,
    clear_autocad_state,
    iter_com_collection,
)


class AutoCADBridge:
    def connect(self, visible=True):
        return False

    def disconnect(self):
        pass

    def get_state(self):
        class State:
            connected = False
            product = "--"
            document = ""
            error = "AutoCAD SDK bridge not wired yet"

        return State()

    def active_layout_name(self):
        return "--"


acad = AutoCADBridge()


__all__ = [
    "acad",
    "AutoCADSession",
    "init_com_for_thread",
    "uninit_com_for_thread",
    "retry_busy_call",
    "wait_until_quiet",
    "get_attr_retry",
    "call_method_retry",
    "clear_autocad_state",
    "iter_com_collection",
]
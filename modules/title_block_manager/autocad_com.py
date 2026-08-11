import time


try:
    import pythoncom
    PYTHONCOM_AVAILABLE = True
except ImportError:
    pythoncom = None
    PYTHONCOM_AVAILABLE = False


COM_RETRY_ATTEMPTS = 50
COM_RETRY_DELAY = 0.5
COM_TIMEOUT_DEFAULT = 90.0
COM_TIMEOUT_SAVE = 180.0
COM_POLL_INTERVAL = 0.2

RPC_E_CALL_REJECTED = 0x80010001
RPC_E_SERVERCALL_RETRYLATER = 0x8001010A


def init_com_for_thread() -> None:
    """Initialize COM for the current thread."""
    if PYTHONCOM_AVAILABLE:
        pythoncom.CoInitialize()


def uninit_com_for_thread() -> None:
    """Uninitialize COM for the current thread."""
    if PYTHONCOM_AVAILABLE:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def pump_com_messages() -> None:
    """Pump COM messages to keep AutoCAD responsive."""
    if PYTHONCOM_AVAILABLE:
        try:
            pythoncom.PumpWaitingMessages()
        except Exception:
            pass


def get_hresult(error: Exception) -> int | None:
    """Extract HRESULT from a COM exception when available."""
    try:
        return error.hresult
    except Exception:
        pass

    try:
        return error.args[0]
    except Exception:
        return None


def is_busy_com_error(error: Exception) -> bool:
    """Return True if AutoCAD rejected the COM call because it is busy."""
    hresult = get_hresult(error)
    return hresult in {
        RPC_E_CALL_REJECTED,
        RPC_E_SERVERCALL_RETRYLATER,
    }


def wait_until_quiet(
    acad,
    timeout: float = COM_TIMEOUT_DEFAULT,
    poll: float = COM_POLL_INTERVAL,
) -> bool:
    """Wait for AutoCAD to become responsive."""
    deadline = time.time() + timeout

    while time.time() < deadline:
        pump_com_messages()

        try:
            _ = acad.Documents.Count
            return True
        except Exception as e:
            if not is_busy_com_error(e):
                return False

            time.sleep(poll)

    return False


def retry_busy_call(
    fn,
    *args,
    retries: int = COM_RETRY_ATTEMPTS,
    delay: float = COM_RETRY_DELAY,
    **kwargs,
):
    """Retry an AutoCAD COM call when AutoCAD reports it is busy."""
    last_error = None

    for _ in range(retries):
        pump_com_messages()

        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_error = e

            if not is_busy_com_error(e):
                raise

            time.sleep(delay)

    raise last_error


def get_attr_retry(
    obj,
    name: str,
    retries: int = COM_RETRY_ATTEMPTS,
    delay: float = COM_RETRY_DELAY,
):
    """Read a COM attribute with retry handling."""
    return retry_busy_call(
        lambda: getattr(obj, name),
        retries=retries,
        delay=delay,
    )


def call_method_retry(
    obj,
    method_name: str,
    *args,
    retries: int = COM_RETRY_ATTEMPTS,
    delay: float = COM_RETRY_DELAY,
    **kwargs,
):
    """Call a COM method with retry handling."""
    method = get_attr_retry(obj, method_name, retries=retries, delay=delay)
    return retry_busy_call(
        method,
        *args,
        retries=retries,
        delay=delay,
        **kwargs,
    )


def clear_autocad_state(acad) -> None:
    """Close all open documents without saving."""
    try:
        documents = acad.Documents

        while documents.Count > 0:
            doc = documents.Item(0)
            retry_busy_call(doc.Close, False)
            time.sleep(0.2)

    except Exception:
        pass
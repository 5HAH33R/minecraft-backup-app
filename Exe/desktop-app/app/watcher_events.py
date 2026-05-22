import threading

_resync_event = threading.Event()


def trigger_resync():
    _resync_event.set()


def check_and_consume_resync() -> bool:
    if _resync_event.is_set():
        _resync_event.clear()
        return True
    return False

"""
Shared state between the download code and the GUI: progress events going up,
and a stop request coming down. It has no Qt dependency.
"""

import threading


class DownloadCancelled(KeyboardInterrupt):
    """
    Raised when the user stops a download.

    It derives from KeyboardInterrupt, not Exception, so the per-file
    `except Exception` handlers cannot swallow it, and the existing Ctrl+C
    cleanup of partial files applies.
    """


_cancel_event = threading.Event()
_listener = None


def reset(listener=None):
    """Prepare for a new download. listener(event_dict) receives the events."""
    global _listener
    _cancel_event.clear()
    _listener = listener


def emit(event_type, **fields):
    if _listener is not None:
        _listener(dict(fields, type=event_type))


def request_cancel():
    _cancel_event.set()


def check_cancelled():
    if _cancel_event.is_set():
        raise DownloadCancelled()


def wait(seconds):
    """Sleep for the given time, waking immediately if a stop is requested."""
    _cancel_event.wait(seconds)
    check_cancelled()

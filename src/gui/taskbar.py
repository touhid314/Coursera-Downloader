"""
Progress on the app's Windows taskbar button, through the ITaskbarList3 COM
interface (Qt 6 no longer provides this). Does nothing on other systems or if
the interface is unavailable.
"""

import ctypes
import sys

NO_PROGRESS = 0
INDETERMINATE = 0x1
NORMAL = 0x2
ERROR = 0x4
PAUSED = 0x8

_CLSID_TASKBAR_LIST = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
_IID_TASKBAR_LIST3 = "{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}"
_CLSCTX_INPROC_SERVER = 0x1

# Positions in the ITaskbarList3 method table (after IUnknown's three methods).
_HR_INIT = 3
_SET_PROGRESS_VALUE = 9
_SET_PROGRESS_STATE = 10


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _guid(text):
    guid = _GUID()
    ctypes.windll.ole32.CLSIDFromString(ctypes.c_wchar_p(text), ctypes.byref(guid))
    return guid


class TaskbarProgress:
    def __init__(self, window):
        self._window = window
        self._taskbar = None
        if sys.platform != "win32":
            return
        try:
            ctypes.windll.ole32.CoInitialize(None)  # already done by Qt is fine
            taskbar = ctypes.c_void_p()
            result = ctypes.windll.ole32.CoCreateInstance(
                ctypes.byref(_guid(_CLSID_TASKBAR_LIST)), None,
                _CLSCTX_INPROC_SERVER, ctypes.byref(_guid(_IID_TASKBAR_LIST3)),
                ctypes.byref(taskbar),
            )
            if result != 0 or not taskbar:
                return
            self._taskbar = taskbar
            self._method(_HR_INIT)(self._taskbar)
        except (OSError, AttributeError):
            self._taskbar = None

    def _method(self, index, *argument_types):
        table = ctypes.cast(
            self._taskbar, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
        ).contents
        prototype = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argument_types)
        return prototype(table[index])

    def _window_handle(self):
        return ctypes.c_void_p(int(self._window.winId()))

    def set_state(self, state):
        if self._taskbar:
            self._method(_SET_PROGRESS_STATE, ctypes.c_void_p, ctypes.c_int)(
                self._taskbar, self._window_handle(), state
            )

    def set_value(self, fraction):
        if self._taskbar:
            self._method(
                _SET_PROGRESS_VALUE, ctypes.c_void_p, ctypes.c_ulonglong, ctypes.c_ulonglong
            )(self._taskbar, self._window_handle(), int(fraction * 1000), 1000)

# limitation of this code is:
# if the user logout of chrome, the cauth cookie doesn't get deleted.
# the prev cauth remains on the file, but it creates a authorization error.
# but if the user logs in again, the cookie is updated


'''
Proof of concept way to get cookies from chrome on Windows.. even when they're locked.
Does not require admin rights.

Includes a pure-python version of release_file_lock from:
https://github.com/thewh1teagle/rookie/blob/02995bbbb692f775e12368e7fb2b728775c88ddd/rookie-rs/src/winapi.rs#L63

(C) - MIT License 2023 - Charles Machalow
'''
import os
from ctypes import windll, byref, create_unicode_buffer, pointer, WINFUNCTYPE
from ctypes.wintypes import DWORD, WCHAR, UINT
import browser_cookie3 # pip install browser-cookie3
import backoff # pip install backoff

ERROR_SUCCESS = 0
ERROR_MORE_DATA  = 234
RmForceShutdown = 1

cookies_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies")

rstrtmgr = windll.LoadLibrary("Rstrtmgr")

@WINFUNCTYPE(None, UINT)
def callback(percent_complete: UINT) -> None:
    # print(f"Unlocking file status: {percent_complete}% done")
    pass

def unlock_cookies():
    session_handle = DWORD(0)
    session_flags = DWORD(0)
    session_key = (WCHAR * 256)()

    result = DWORD(rstrtmgr.RmStartSession(byref(session_handle), session_flags, session_key)).value

    if result != ERROR_SUCCESS:
        raise RuntimeError(f"RmStartSession returned non-zero result: {result}")

    try:
        result = DWORD(rstrtmgr.RmRegisterResources(session_handle, 1, byref(pointer(create_unicode_buffer(cookies_path))), 0, None, 0, None)).value

        if result != ERROR_SUCCESS:
            raise RuntimeError(f"RmRegisterResources returned non-zero result: {result}")

        proc_info_needed = DWORD(0)
        proc_info = DWORD(0)
        reboot_reasons = DWORD(0)

        result = DWORD(rstrtmgr.RmGetList(session_handle, byref(proc_info_needed), byref(proc_info), None, byref(reboot_reasons))).value

        if result not in (ERROR_SUCCESS, ERROR_MORE_DATA):
            raise RuntimeError(f"RmGetList returned non-successful result: {result}")

        if proc_info_needed.value:
            result = DWORD(rstrtmgr.RmShutdown(session_handle, RmForceShutdown, callback)).value

            if result != ERROR_SUCCESS:
                raise RuntimeError(f"RmShutdown returned non-successful result: {result}")
        else:
            # print("File is not locked")
            pass
    finally:
        result = DWORD(rstrtmgr.RmEndSession(session_handle)).value

        if result != ERROR_SUCCESS:
            raise RuntimeError(f"RmEndSession returned non-successful result: {result}")


# Use backoff here since there is a race condition between unlocking the file and reading it.
# Technically we're killing a process within chrome that holds the lock. Chrome can/will restart it,
# .. so we have to fetch cookies before it re-locks the file. Generally on my system we get them
# .... though one time we didn't. I think it has to do with opening a new tab.. idk. Maybe not necessary?

@backoff.on_exception(backoff.constant, PermissionError, max_tries=5)
def fetch_locked_cookies(domain):
    unlock_cookies()
    # return browser_cookie3.chrome(cookies_path)
    return browser_cookie3.chrome(domain_name=domain)

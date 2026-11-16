import base64
import os
import sys
import time

from .. import paths


RESULT_PREFIX = "COURsera_AUTH::"
ERROR_PREFIX = "COURsera_ERROR::"


def _send_result(prefix, value, result_path=None):
    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    message = f"{prefix}{encoded}"
    if result_path:
        with open(result_path, "w", encoding="utf-8") as result_file:
            result_file.write(message)
        return
    print(message, flush=True)


def _cookie_value(cookies, name):
    for cookie_group in cookies or []:
        if isinstance(cookie_group, dict) and name in cookie_group:
            cookie = cookie_group[name]
            return getattr(cookie, "value", str(cookie))

        cookie_name = getattr(cookie_group, "key", None) or getattr(
            cookie_group, "name", None
        )
        if cookie_name == name:
            return getattr(cookie_group, "value", "")
    return ""


def _write_cookie_names(cookies, path):
    names = set()
    for cookie_group in cookies or []:
        if isinstance(cookie_group, dict):
            names.update(cookie_group.keys())
    with open(path, "w", encoding="utf-8") as names_file:
        names_file.write(" ".join(sorted(names)))


def _webview_backend():
    """WebView2 on Windows, Qt WebEngine on Linux, WebKit (the default) on macOS."""
    if sys.platform == "win32":
        return "edgechromium"
    if sys.platform.startswith("linux"):
        return "qt"
    return None


def run_webview_login(result_path=None):
    """Run the Coursera login window in its own process."""
    try:
        if sys.platform.startswith("linux"):
            # pywebview's Qt backend, on the PySide6 the app already ships.
            os.environ.setdefault("QT_API", "pyside6")
        import webview

        storage_path = os.path.join(paths.user_data_dir(), "WebView2")
        os.makedirs(storage_path, exist_ok=True)
        window = webview.create_window(
            "Log in to Coursera",
            "https://www.coursera.org/?authMode=login",
            width=1000,
            height=720,
            min_size=(700, 500),
        )

        from ..services.general import check_cauth

        # The release workflow checks that cookies can be read from the window,
        # without a real login: it gets the cookie names (never their values).
        cookie_names_file = os.environ.get("SMOKE_TEST_COOKIE_NAMES_FILE")

        def watch_for_login(login_window):
            # The window keeps its cookies between runs, so it may still hold
            # an expired login. Wait until Coursera accepts the cookie.
            rejected = set()
            while True:
                try:
                    cookies = login_window.get_cookies()
                    if cookie_names_file:
                        _write_cookie_names(cookies, cookie_names_file)
                    cauth_cookie = _cookie_value(cookies, "CAUTH")
                    if cauth_cookie and cauth_cookie not in rejected:
                        if check_cauth(cauth_cookie) is False:
                            rejected.add(cauth_cookie)
                            continue
                        _send_result(RESULT_PREFIX, cauth_cookie, result_path)
                        login_window.destroy()
                        return
                except Exception:
                    pass
                time.sleep(1)

        webview.start(
            watch_for_login,
            window,
            gui=_webview_backend(),
            private_mode=False,
            storage_path=storage_path,
        )
        return 0
    except Exception as exc:
        _send_result(ERROR_PREFIX, str(exc), result_path)
        return 1

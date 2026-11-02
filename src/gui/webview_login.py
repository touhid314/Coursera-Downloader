import base64
import os
import time


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


def run_webview_login(result_path=None):
    """Run WebView2 in its own process and return the resulting CAUTH cookie."""
    try:
        import webview

        storage_path = os.path.join(
            os.environ.get("APPDATA", os.getcwd()),
            "CourseraDownloader",
            "WebView2",
        )
        window = webview.create_window(
            "Log in to Coursera",
            "https://www.coursera.org/?authMode=login",
            width=1000,
            height=720,
            min_size=(700, 500),
        )

        from ..services.general import check_cauth

        def watch_for_login(login_window):
            # The window keeps its cookies between runs, so it may still hold
            # an expired login. Wait until Coursera accepts the cookie.
            rejected = set()
            while True:
                try:
                    cauth_cookie = _cookie_value(
                        login_window.get_cookies(), "CAUTH"
                    )
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
            gui="edgechromium",
            private_mode=False,
            storage_path=storage_path,
        )
        return 0
    except Exception as exc:
        _send_result(ERROR_PREFIX, str(exc), result_path)
        return 1

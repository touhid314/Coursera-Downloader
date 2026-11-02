import base64
import os
import tempfile
from http.cookies import SimpleCookie
from types import SimpleNamespace
from unittest import TestCase, mock

import requests

from src.gui import webview_login
from src.services import general


class AuthenticationTests(TestCase):
    @mock.patch("src.services.general.requests.get")
    def test_check_cauth_accepts_success(self, get):
        get.return_value = SimpleNamespace(status_code=200, ok=True)

        self.assertIs(general.check_cauth("valid-cookie"), True)
        get.assert_called_once_with(
            general.LOGIN_CHECK_URL,
            cookies={"CAUTH": "valid-cookie"},
            timeout=15,
        )

    @mock.patch("src.services.general.requests.get")
    def test_check_cauth_rejects_unauthorized_cookie(self, get):
        for status_code in (401, 403):
            with self.subTest(status_code=status_code):
                get.return_value = SimpleNamespace(status_code=status_code, ok=False)
                self.assertIs(general.check_cauth("expired-cookie"), False)

    @mock.patch("src.services.general.requests.get")
    def test_check_cauth_keeps_session_when_result_is_inconclusive(self, get):
        get.side_effect = requests.ConnectionError("offline")
        self.assertIsNone(general.check_cauth("unknown-cookie"))

        get.side_effect = None
        get.return_value = SimpleNamespace(status_code=500, ok=False)
        self.assertIsNone(general.check_cauth("unknown-cookie"))

    def test_extracts_cauth_from_webview_cookie(self):
        cookie = SimpleCookie()
        cookie["CAUTH"] = "coursera-session"

        self.assertEqual(
            webview_login._cookie_value([cookie], "CAUTH"),
            "coursera-session",
        )

    @mock.patch("src.services.general.check_cauth", return_value=True)
    def test_embedded_login_uses_persistent_profile(self, _check_cauth):
        cookie = SimpleCookie()
        cookie["CAUTH"] = "persisted-session"
        window = mock.Mock()
        window.get_cookies.return_value = [cookie]
        fake_webview = SimpleNamespace()
        fake_webview.create_window = mock.Mock(return_value=window)

        def start(callback, callback_window, **options):
            self.assertIs(callback_window, window)
            self.assertIs(options["private_mode"], False)
            self.assertTrue(options["storage_path"].endswith(
                os.path.join("CourseraDownloader", "WebView2")
            ))
            callback(callback_window)

        fake_webview.start = mock.Mock(side_effect=start)
        with tempfile.TemporaryDirectory() as temporary_directory:
            result_path = os.path.join(temporary_directory, "login-result.txt")
            with mock.patch.dict("sys.modules", {"webview": fake_webview}), \
                    mock.patch.dict(os.environ, {"APPDATA": os.path.join("C:\\", "Profile")}):
                result = webview_login.run_webview_login(result_path)

            with open(result_path, encoding="utf-8") as result_file:
                output = result_file.read()

        self.assertEqual(result, 0)
        window.destroy.assert_called_once_with()
        encoded = output.strip().removeprefix(
            webview_login.RESULT_PREFIX
        )
        self.assertEqual(
            base64.b64decode(encoded).decode("utf-8"),
            "persisted-session",
        )

    @mock.patch("src.services.general.keyring")
    def test_embedded_cookie_round_trip_uses_credential_vault(self, keyring):
        keyring.get_password.return_value = "saved-session"

        self.assertTrue(general.save_embedded_auth("saved-session"))
        keyring.set_password.assert_called_once_with(
            general.AUTH_SERVICE,
            general.EMBEDDED_AUTH_ACCOUNT,
            "saved-session",
        )
        self.assertEqual(general.load_embedded_auth(), "saved-session")

        general.clear_embedded_auth()
        keyring.delete_password.assert_called_once_with(
            general.AUTH_SERVICE,
            general.EMBEDDED_AUTH_ACCOUNT,
        )

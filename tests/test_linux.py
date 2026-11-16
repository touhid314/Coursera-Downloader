"""Linux-specific behavior, tested on any system by simulating Linux."""

import os
import sys
import tempfile
from unittest import TestCase, mock

from src import paths
from src.services import general

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def on_linux():
    return mock.patch.object(sys, "platform", "linux")


class LinuxSettingsFileTests(TestCase):
    def test_packaged_app_keeps_settings_in_the_user_data_folder(self):
        with tempfile.TemporaryDirectory() as bundle, tempfile.TemporaryDirectory() as data:
            with open(os.path.join(bundle, "data.bin"), "wb") as f:
                f.write(b"defaults")
            with mock.patch.multiple(
                paths, IS_MACOS=False, IS_WINDOWS=False, APP_ROOT=bundle
            ), mock.patch.object(sys, "frozen", True, create=True), on_linux(), \
                    mock.patch.dict(os.environ, {"XDG_DATA_HOME": data}):
                settings = paths.app_file("data.bin")
            self.assertEqual(settings, os.path.join(data, "CourseraDownloader", "data.bin"))
            with open(settings, "rb") as f:
                self.assertEqual(f.read(), b"defaults")


class LinuxUpdateTests(TestCase):
    def test_update_link_goes_to_the_linux_install_page(self):
        with on_linux():
            self.assertEqual(general.update_page_url("x.exe"), general.LINUX_INSTALL_PAGE)
            self.assertEqual(general.install_command(), general.LINUX_INSTALL_COMMAND)

    def test_install_command_matches_the_script_and_readme(self):
        for name in ("install-linux.sh", "README.md"):
            with open(os.path.join(ROOT, name), encoding="utf-8") as f:
                self.assertIn(general.LINUX_INSTALL_COMMAND, f.read(), name)

    def test_update_script_runs_the_install_command_and_waits(self):
        with on_linux():
            path = general.write_update_script()
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        self.assertTrue(path.endswith(".sh"))
        with open(path, encoding="utf-8") as f:
            script = f.read()
        self.assertIn(general.LINUX_INSTALL_COMMAND + "\n", script)
        self.assertIn("read -r", script)  # the window stays open

    def test_runs_the_script_in_the_first_terminal_found(self):
        found = {"gnome-terminal": "/usr/bin/gnome-terminal", "xterm": "/usr/bin/xterm"}
        with mock.patch("shutil.which", side_effect=found.get):
            self.assertEqual(
                general.linux_terminal_command("/tmp/u.sh"),
                ["/usr/bin/gnome-terminal", "--", "bash", "/tmp/u.sh"],
            )

    def test_no_terminal(self):
        with mock.patch("shutil.which", return_value=None):
            self.assertIsNone(general.linux_terminal_command("/tmp/u.sh"))


class LinuxBrowserTests(TestCase):
    def test_opens_brave_by_its_command(self):
        found = {"brave-browser": "/usr/bin/brave-browser"}
        with on_linux(), mock.patch("shutil.which", side_effect=found.get), \
                mock.patch("subprocess.Popen") as popen:
            self.assertTrue(general.open_browser("brave", "https://www.coursera.org"))
        self.assertEqual(
            popen.call_args.args[0], ["/usr/bin/brave-browser", "https://www.coursera.org"]
        )

    def test_reports_a_browser_that_is_not_installed(self):
        with on_linux(), mock.patch("shutil.which", return_value=None):
            self.assertFalse(general.open_browser("firefox", "https://www.coursera.org"))

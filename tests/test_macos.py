"""macOS-specific behavior, tested on any system by simulating macOS."""

import importlib
import os
import subprocess
import sys
import tempfile
from unittest import TestCase, mock

from src import paths
from src.services import general


class MacSettingsFileTests(TestCase):
    def setUp(self):
        self.bundle = tempfile.TemporaryDirectory()
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.bundle.cleanup)
        self.addCleanup(self.home.cleanup)
        with open(os.path.join(self.bundle.name, "data.bin"), "wb") as f:
            f.write(b"bundled defaults")

    def mac_app(self):
        """Simulate the packaged Mac app."""
        return mock.patch.multiple(
            paths, IS_MACOS=True, APP_ROOT=self.bundle.name
        ), mock.patch.object(sys, "frozen", True, create=True), mock.patch(
            "os.path.expanduser",
            side_effect=lambda p: p.replace("~", self.home.name, 1),
        )

    def test_settings_live_outside_the_app_bundle(self):
        patch_paths, patch_frozen, patch_home = self.mac_app()
        with patch_paths, patch_frozen, patch_home:
            settings = paths.app_file("data.bin")

        self.assertEqual(
            settings,
            os.path.join(
                self.home.name, "Library", "Application Support",
                "CourseraDownloader", "data.bin",
            ),
        )
        with open(settings, "rb") as f:
            self.assertEqual(f.read(), b"bundled defaults")

    def test_existing_settings_are_kept(self):
        patch_paths, patch_frozen, patch_home = self.mac_app()
        with patch_paths, patch_frozen, patch_home:
            settings = paths.app_file("data.bin")
            with open(settings, "wb") as f:
                f.write(b"user settings")
            self.assertEqual(paths.app_file("data.bin"), settings)

        with open(settings, "rb") as f:
            self.assertEqual(f.read(), b"user settings")

    def test_running_from_source_uses_the_project_folder(self):
        with mock.patch.object(paths, "IS_MACOS", True):
            self.assertEqual(
                paths.app_file("data.bin"),
                os.path.join(paths.APP_ROOT, "data.bin"),
            )


class MacBrowserTests(TestCase):
    def test_opens_the_browser_by_application_name(self):
        finished = subprocess.CompletedProcess([], 0)
        with mock.patch.object(sys, "platform", "darwin"), mock.patch(
            "subprocess.run", return_value=finished
        ) as run:
            self.assertTrue(general.open_browser("brave", "https://www.coursera.org"))

        self.assertEqual(
            run.call_args.args[0],
            ["open", "-a", "Brave Browser", "https://www.coursera.org"],
        )

    def test_reports_a_browser_that_is_not_installed(self):
        missing = subprocess.CompletedProcess([], 1)
        with mock.patch.object(sys, "platform", "darwin"), mock.patch(
            "subprocess.run", return_value=missing
        ):
            self.assertFalse(general.open_browser("firefox", "https://www.coursera.org"))


class MacIconTests(TestCase):
    def test_mac_uses_the_png_icon(self):
        with mock.patch.object(sys, "platform", "darwin"):
            mac_paths = importlib.reload(paths)
            self.assertTrue(mac_paths.ICON_FILE.endswith("icon.png"))
            self.assertTrue(os.path.isfile(mac_paths.ICON_FILE))
        importlib.reload(paths)


class MacUpdateTests(TestCase):
    EXE = "https://github.com/x/releases/download/v9/Installer.exe"

    def test_mac_update_link_goes_to_the_mac_install_page(self):
        with mock.patch.object(sys, "platform", "darwin"):
            self.assertEqual(general.update_page_url(self.EXE), general.MACOS_INSTALL_PAGE)

    def test_windows_update_link_is_the_installer(self):
        with mock.patch.object(sys, "platform", "win32"):
            self.assertEqual(general.update_page_url(self.EXE), self.EXE)

    def test_install_command_matches_the_script_and_readme(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for name in ("install-macos.sh", "README.md"):
            with open(os.path.join(root, name), encoding="utf-8") as f:
                self.assertIn(general.MACOS_INSTALL_COMMAND, f.read(), name)

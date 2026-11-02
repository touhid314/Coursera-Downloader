import re
from pathlib import Path
from unittest import TestCase

from src import __version__


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class VersionTests(TestCase):
    def test_release_files_use_the_app_version(self):
        installer = (PROJECT_ROOT / "release/config/installer.iss").read_text(
            encoding="utf-8"
        )
        installer_version = re.search(
            r'^#define AppVersion "([^"]+)"$', installer, re.MULTILINE
        )

        self.assertIsNotNone(installer_version)
        self.assertEqual(installer_version.group(1), __version__)

    def test_current_version_is_in_changelog(self):
        changelog = (PROJECT_ROOT / "changelog.md").read_text(encoding="utf-8")

        self.assertIn(f"## v{__version__}", changelog)

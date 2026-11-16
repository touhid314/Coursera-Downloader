# Release workspace

Everything needed to build and publish the Windows and macOS apps lives here. Generated
files and historical releases are kept separate from the active configuration.

## Folder layout

| Path | Purpose | Keep in Git? |
| --- | --- | --- |
| `build_app.bat` | Builds the portable app with PyInstaller. | Yes |
| `build_installer.bat` | Packages the built app with Inno Setup. | Yes |
| `config/` | Active PyInstaller, Inno Setup, and default-data files. | Yes |
| `artifacts/app/` | Generated portable application. | No |
| `artifacts/installers/` | Generated installer for the current release. | No |
| `work/` | Temporary PyInstaller files. | No |
| `archive/` | Old builds, published installers, and retired tooling. | No |

## Requirements

- Python and the project dependencies
- PyInstaller (`pip install -r requirements-dev.txt`)
- [Inno Setup 6](https://jrsoftware.org/isinfo.php)

Run all commands from the project root.

## Create a release

1. Update the version in both places:
   - `src/__init__.py`
   - `release/config/installer.iss` (`AppVersion` at the top)
2. Add the user-visible changes to `changelog.md`.
3. Run the automated tests:

   ```powershell
   .venv\Scripts\python.exe -m unittest discover -s tests -v
   ```

4. Run `release\build_app.bat`.
5. Test `release\artifacts\app\CourseraDownloader\CourseraDownloader.exe`.
6. Run `release\build_app.bat` again after testing. The app stores settings in
   its bundled `data.bin`, so the final artifact should be a fresh build.
7. Run `release\build_installer.bat`.
8. Install the generated setup file on a clean or disposable Windows account
   and verify login, course listing, downloading, and uninstalling.
9. Commit and push the release changes.
10. Tag the commit and push the tag:

    ```powershell
    git tag -a v4.0.0 -m "Release v4.0.0"
    git push origin v4.0.0
    ```

11. Pushing the tag starts `.github/workflows/release.yml`. It runs the tests,
    builds the portable app and installer on Windows and the Apple silicon and
    Intel disk images on macOS, smoke-tests the installed Mac app, and creates
    the GitHub release with all downloads and their SHA-256 checksums. If the
    release already exists, it adds or replaces the downloads.
12. Update the project website's download link to the new GitHub release and
    verify the public download from a browser.

Replace `4.0.0` in the example tag when preparing a later release.

## macOS builds

macOS builds need a Mac, so they are made by the workflow. To build and test
without publishing, run **Actions → Release → Run workflow** on any branch;
the builds appear as artifacts of that run. On a Mac, the same build can be
made locally:

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m PyInstaller release/config/pyinstaller.spec --noconfirm --clean   --distpath release/artifacts/app --workpath release/work
release/artifacts/app/CourseraDownloader.app/Contents/MacOS/CourseraDownloader --smoke-test
```

The app is signed ad hoc, not with an Apple Developer ID, and is not
notarized. Users install it with `install-macos.sh` (see the README), which
downloads with curl so the app is not quarantined and opens without a security
warning. The script picks the newest release's `-macos-<arch>.dmg`, so keep
that file name pattern. After each release, the workflow runs
`.github/workflows/macos-install-test.yml` to install the published release
with the script on both Mac architectures. The packaged Mac app keeps its settings in
`~/Library/Application Support/CourseraDownloader`, not in the bundle.

## Notes

- `config/default_data/data.bin` must never contain a personal Coursera cookie.
- Inno Setup upgrades the existing installation. The installer script does not
  manually delete the installation directory.
- InstallForge is retired because it produced unreliable installers. Its old
  project files remain under `archive/legacy_tooling/` for reference only.
- `archive/` is historical reference material, not part of the current build.

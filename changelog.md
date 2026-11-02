# Changelog

## v4.0.0

This is a substantial modernization of the application, its authentication
flow, download experience, internal structure, testing, and Windows release
process.

### Added

- Embedded Coursera login powered by WebView2, with a persistent browser profile
  and secure credential storage through the Windows credential vault.
- Automatic loading of enrolled courses after login.
- Direct support for course, specialization, and professional-certificate URLs.
- Multi-course specialization downloads.
- In-app progress showing the current file, file counts, percentage, downloaded
  size, speed, and course progress.
- Windows taskbar progress and download-completion notifications.
- Stop and resume controls, including continuation of partial files.
- Downloads for quizzes and notebooks alongside the existing course resources.
- Automated tests for authentication, persistent login, and course-link parsing.
- Dedicated source launcher and a reorganized Windows build and release system.

### Changed

- Migrated the desktop interface from PyQt5 to PySide6.
- Redesigned the interface to scale cleanly across window sizes and high-DPI
  displays, while following the system's light or dark colors.
- Downloads now run in a worker thread so the interface remains responsive.
- Authentication cookies are kept out of the ordinary settings database.
- The application code is organized into `src/gui`, `src/core`, and
  `src/services` packages.
- All release configuration, generated artifacts, historical installers, and
  documentation are organized under `release/`.
- PyInstaller and Inno Setup now have separate, repeatable build scripts.

### Fixed

- Embedded-browser sessions being lost shortly after login or between launches.
- Download folders containing spaces or other normal Windows path characters.
- Accidental command-line usage output when a folder or course was not selected.
- Login validation incorrectly discarding a session during temporary network
  failures.
- Window layout and text clipping problems on high-DPI displays.
- Download errors and cancellation leaving the interface in an unclear state.

## v3.0.1

- Fixed interface scaling on high-DPI displays.

## v3.0.0

- Replaced the Tkinter interface with PyQt.
- Added application update checks and remote notifications.
- Added anonymous usage measurement.
- Switched browser-cookie access from `browsercookie3` to `rookiepy`.
- Fixed download paths containing spaces.
- Fixed the Chinese subtitle language code.
- Reorganized the repository and refreshed the interface.

## v2.1.0

- Improved browser-cookie permission handling for Chrome and Edge.
- Added the application menu and additional error handling.
- Fixed course-name extraction from Coursera URLs.

## v2.0.0

- Adopted the downloader fork maintained by
  [raffaem](https://github.com/raffaem/cs-dlp).

## v1.0.0

- Initial GUI release based on `coursera-dl`.

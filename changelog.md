# Changelog

## v4.1.0

### Added

- **1080p** video option (#18). Few Coursera courses have 1080p videos; other
  videos are downloaded in the highest quality they have, usually 720p.
- **Paste login cookie** login option: paste the CAUTH cookie from any browser
  when the embedded and browser logins don't work (#14). It is checked with
  Coursera and stored in the Windows credential vault.
- The download summary now says how many quizzes and graded assignments were
  not downloaded. Coursera's current quiz format (#10) can't be downloaded,
  because its questions only appear after starting an attempt.

### Fixed

- When the chosen resolution wasn't available, the fallback picked 720p even
  for videos that have 1080p, because resolutions were compared as text.
- One course item that Coursera answers unexpectedly no longer stops the whole
  course; it is reported and the rest of the course downloads (#4).
- Reading the login from Brave or Firefox could crash the app with a Rust
  `PanicException`; it now shows a login error instead (#13).
- Malay subtitles used Malayalam's language code, so Malay could not be
  selected or saved correctly (#16). Corrected the spelling of Portuguese and
  Telugu.

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

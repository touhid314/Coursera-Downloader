#!/bin/bash
# Install or update Coursera Full Course Downloader on Linux (x86-64).
#
#   curl -fsSL https://raw.githubusercontent.com/touhid314/Coursera-Downloader/main/install-linux.sh | bash
#
# Downloads the latest release into ~/.local/share/coursera-downloader, adds
# it to the applications menu and adds the "coursera-downloader" command to
# ~/.local/bin. No administrator rights are needed.

set -euo pipefail

REPO="touhid314/Coursera-Downloader"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
INSTALL_DIR="$DATA_HOME/coursera-downloader"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/coursera-downloader"
DESKTOP_FILE="$DATA_HOME/applications/coursera-downloader.desktop"

fail() {
    echo "Error: $*" >&2
    exit 1
}

[ "$(uname -s)" = "Linux" ] || fail "this installer is for Linux."
[ "$(uname -m)" = "x86_64" ] || fail "only 64-bit Intel/AMD (x86-64) Linux is supported; this is $(uname -m)."
command -v curl >/dev/null || fail "curl is required."
command -v tar >/dev/null || fail "tar is required."

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if [ -n "${COURSERA_DL_ARCHIVE:-}" ]; then
    # For testing a build before it is published.
    cp "$COURSERA_DL_ARCHIVE" "$work/app.tar.gz" || fail "cannot read $COURSERA_DL_ARCHIVE."
else
    echo "Finding the latest release..."
    release=$(curl -fsSL -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/$REPO/releases/latest") \
        || fail "could not reach GitHub. Check your internet connection."
    url=$(printf '%s\n' "$release" \
        | grep -o '"browser_download_url": *"[^"]*-linux-x86_64\.tar\.gz"' \
        | head -n 1 | sed 's/.*"\(https[^"]*\)"/\1/')
    [ -n "$url" ] || fail "the latest release has no Linux download."
    echo "Downloading $(basename "$url")..."
    curl -fL --progress-bar -o "$work/app.tar.gz" "$url" || fail "the download failed."
fi
mkdir -p "$work/app"
tar -xzf "$work/app.tar.gz" -C "$work/app" || fail "could not unpack the download."
[ -x "$work/app/CourseraDownloader/CourseraDownloader" ] || fail "the download is incomplete."

# Close a running copy before replacing it.
if pgrep -x CourseraDownloader >/dev/null; then
    echo "Closing the running Coursera Downloader..."
    pkill -x CourseraDownloader || true
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        pgrep -x CourseraDownloader >/dev/null || break
        sleep 1
    done
fi

echo "Installing to $INSTALL_DIR..."
rm -rf "$INSTALL_DIR"
mkdir -p "$(dirname "$INSTALL_DIR")"
mv "$work/app/CourseraDownloader" "$INSTALL_DIR"

icon=$(find "$INSTALL_DIR" -path '*assets/icon/icon.png' | head -n 1)
mkdir -p "$BIN_DIR" "$(dirname "$DESKTOP_FILE")"
ln -sf "$INSTALL_DIR/CourseraDownloader" "$LAUNCHER"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Coursera Full Course Downloader
Comment=Download complete Coursera courses
Exec="$INSTALL_DIR/CourseraDownloader"
Icon=$icon
Terminal=false
Categories=Network;Education;
StartupWMClass=CourseraDownloader
EOF
chmod +x "$DESKTOP_FILE"
command -v update-desktop-database >/dev/null \
    && update-desktop-database "$(dirname "$DESKTOP_FILE")" >/dev/null 2>&1 || true

echo "Coursera Full Course Downloader is installed."
echo "Open it from the applications menu, or run: coursera-downloader"

# Qt needs a few system libraries that most desktops have; say which are missing.
missing=$(LD_LIBRARY_PATH="$INSTALL_DIR/_internal" ldd \
    "$INSTALL_DIR"/_internal/PySide6/Qt/plugins/platforms/libqxcb.so 2>/dev/null \
    | grep "not found" | awk '{print $1}' | sort -u | tr '\n' ' ' || true)
if [ -n "$missing" ]; then
    echo
    echo "Note: these system libraries are missing: $missing"
    echo "On Ubuntu or Debian, install them with:"
    echo "  sudo apt install libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libegl1"
fi

if [ -z "${COURSERA_DL_NO_OPEN:-}" ] && { [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; }; then
    nohup "$INSTALL_DIR/CourseraDownloader" >/dev/null 2>&1 &
fi

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

# Close a running copy before replacing it. Processes are matched by their
# program file: names are cut to 15 characters, and the command line shows
# whichever path (such as the coursera-downloader link) started it.
app_pids() {
    for proc in /proc/[0-9]*; do
        [ "$(readlink "$proc/exe" 2>/dev/null)" = "$INSTALL_DIR/CourseraDownloader" ] \
            && echo "${proc#/proc/}"
    done
    return 0
}
pids=$(app_pids)
if [ -n "$pids" ]; then
    echo "Closing the running Coursera Downloader..."
    kill $pids 2>/dev/null || true
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        [ -z "$(app_pids)" ] && break
        sleep 1
    done
    pids=$(app_pids)
    [ -n "$pids" ] && kill -9 $pids 2>/dev/null || true
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

# The window (Qt) and the login window (Qt WebEngine) need some system
# libraries that desktops have; say which are missing.
internal="$INSTALL_DIR/_internal"
missing=$(for file in \
        "$internal/PySide6/Qt/plugins/platforms/libqxcb.so" \
        "$internal/libQt6WebEngineCore.so.6" \
        "$internal/PySide6/Qt/libexec/QtWebEngineProcess"; do
    [ -e "$file" ] && LD_LIBRARY_PATH="$internal:$internal/PySide6/Qt/lib" ldd "$file" 2>/dev/null
done | grep "not found" | awk '{print $1}' | sort -u | tr '\n' ' ' || true)
if [ -n "$missing" ]; then
    echo
    echo "Note: these system libraries are missing: $missing"
    echo "On Ubuntu or Debian, this installs the usual ones:"
    echo "  sudo apt install libegl1 libgl1 libnss3 libxcomposite1 libxdamage1 libxrandr2 libxtst6 libxkbfile1 libfontconfig1 libdbus-1-3"
fi

if [ -z "${COURSERA_DL_NO_OPEN:-}" ] && { [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; }; then
    nohup "$INSTALL_DIR/CourseraDownloader" >/dev/null 2>&1 &
fi

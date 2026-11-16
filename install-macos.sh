#!/bin/bash
# Install or update Coursera Full Course Downloader on macOS.
#
#   curl -fsSL https://raw.githubusercontent.com/touhid314/Coursera-Downloader/main/install-macos.sh | bash
#
# Downloads the latest release for this Mac (Apple silicon or Intel) and
# copies the app to /Applications. A download made with curl is not marked as
# coming from the internet, so macOS opens the app without the "cannot check
# it for malware" warning.

set -euo pipefail

REPO="touhid314/Coursera-Downloader"
APP_NAME="Coursera Downloader.app"

fail() {
    echo "Error: $*" >&2
    exit 1
}

[ "$(uname -s)" = "Darwin" ] || fail "this installer is for macOS."

macos_major=$(sw_vers -productVersion | cut -d. -f1)
[ "$macos_major" -ge 13 ] || fail "macOS 13 Ventura or newer is required (this Mac has $(sw_vers -productVersion))."

# A Terminal running under Rosetta reports x86_64 on Apple silicon, so ask
# the hardware.
if [ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" = "1" ]; then
    arch="arm64"
    chip="Apple silicon"
else
    arch="x86_64"
    chip="Intel"
fi

echo "Finding the latest release for $chip Macs..."
release=$(curl -fsSL -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$REPO/releases/latest") \
    || fail "could not reach GitHub. Check your internet connection."
url=$(printf '%s\n' "$release" \
    | grep -o '"browser_download_url": *"[^"]*-macos-'"$arch"'\.dmg"' \
    | head -n 1 | sed 's/.*"\(https[^"]*\)"/\1/')
[ -n "$url" ] || fail "the latest release has no download for $chip Macs."

work=$(mktemp -d)
mount_point="$work/mount"
cleanup() {
    hdiutil detach "$mount_point" -quiet >/dev/null 2>&1 || true
    rm -rf "$work"
}
trap cleanup EXIT

echo "Downloading $(basename "$url")..."
curl -fL --progress-bar -o "$work/app.dmg" "$url" || fail "the download failed."

mkdir -p "$mount_point"
hdiutil attach "$work/app.dmg" -nobrowse -readonly -quiet -mountpoint "$mount_point" \
    || fail "could not open the disk image."

# /Applications if this user may write to it, otherwise ~/Applications.
target_dir="/Applications"
if [ ! -w "$target_dir" ]; then
    target_dir="$HOME/Applications"
    mkdir -p "$target_dir"
fi
target="$target_dir/$APP_NAME"

# Close a running copy before replacing it.
if pgrep -xq CourseraDownloader; then
    echo "Closing the running Coursera Downloader..."
    osascript -e 'tell application id "io.github.touhid314.courseradownloader" to quit' >/dev/null 2>&1 || true
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        pgrep -xq CourseraDownloader || break
        sleep 1
    done
    pgrep -xq CourseraDownloader \
        && fail "Coursera Downloader is still open. Close it, then run this command again."
fi

echo "Installing to $target..."
rm -rf "$target"
ditto "$mount_point/$APP_NAME" "$target"
xattr -dr com.apple.quarantine "$target" 2>/dev/null || true

echo "Coursera Full Course Downloader is installed in $target_dir."
if [ -z "${COURSERA_DL_NO_OPEN:-}" ]; then
    open "$target"
fi

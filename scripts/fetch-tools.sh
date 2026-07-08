#!/bin/sh
# fetch-tools.sh — download the kiwix-tools binaries (C1 archive layer).
# We don't vendor third-party binaries in the repo; fetch them from the
# official Kiwix release server instead. https://download.kiwix.org/release/
set -e
VERSION="3.8.2"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64)  PLATFORM="macos-arm64" ;;
  Darwin-x86_64) PLATFORM="macos-x86_64" ;;
  Linux-x86_64)  PLATFORM="linux-x86_64" ;;
  Linux-aarch64) PLATFORM="linux-aarch64" ;;
  *) echo "unsupported platform: $(uname -s)-$(uname -m)"; exit 1 ;;
esac

NAME="kiwix-tools_${PLATFORM}-${VERSION}"
if [ -x "$REPO/tools/$NAME/kiwix-serve" ]; then
  echo "already present: tools/$NAME"
  exit 0
fi

mkdir -p "$REPO/tools"
echo "fetching $NAME ..."
curl -L --fail "https://download.kiwix.org/release/kiwix-tools/$NAME.tar.gz" \
  | tar -xz -C "$REPO/tools"
echo "done: tools/$NAME/kiwix-serve"

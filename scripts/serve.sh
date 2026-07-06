#!/bin/sh
# Start the archive layer (C1/C2): kiwix-serve over everything in library/master.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$REPO/tools/kiwix-tools_macos-arm64-3.8.2/kiwix-serve"
exec "$BIN" --port 8181 --address 127.0.0.1 "$REPO"/library/master/*.zim

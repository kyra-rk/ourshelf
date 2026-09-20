#!/usr/bin/env bash
#
# open_web.sh
#
# Starts the ourshelf web app's dev server and opens it in the browser.
#
# Usage:
#   bash open_web.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$SCRIPT_DIR/web"
PORT="${PORT:-5173}"
URL="http://localhost:$PORT/"

cd "$WEB_DIR"

if [ ! -d node_modules ]; then
    echo "Installing dependencies..."
    npm install
fi

npm run dev -- --port "$PORT" --strictPort &
DEV_PID=$!
trap 'kill "$DEV_PID" 2>/dev/null' EXIT

echo "Waiting for dev server at $URL..."
for _ in $(seq 1 50); do
    if curl -s -o /dev/null "$URL"; then
        break
    fi
    sleep 0.2
done

case "$(uname -s)" in
    Darwin) open "$URL" ;;
    Linux) xdg-open "$URL" ;;
    *) echo "Open $URL in your browser." ;;
esac

wait "$DEV_PID"

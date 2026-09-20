#!/usr/bin/env bash
#
# clean.sh
#
# Deletes local runtime files: session auth, database, and debug HTML/screenshots.
# Safe to run at any time — does not touch source code, docs, or the committed cache.
#
# Usage:
#   bash clean.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Cleaning runtime files..."

# Goodreads session — will need to re-login after this
if [ -f "$SCRIPT_DIR/auth_state.json" ]; then
    rm "$SCRIPT_DIR/auth_state.json"
    echo "  removed auth_state.json"
fi

# Local database
if [ -f "$SCRIPT_DIR/data/goodreads.db" ]; then
    rm "$SCRIPT_DIR/data/goodreads.db"
    echo "  removed data/goodreads.db"
fi

# Debug HTML and screenshots
find "$SCRIPT_DIR/debug" -name "*.html" -o -name "*.png" 2>/dev/null | while read -r f; do
    rm "$f"
    echo "  removed $f"
done

echo "Done."

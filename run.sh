#!/usr/bin/env bash
#
# run.sh
#
# Full ourshelf pipeline:
#   1. Scrape your own Goodreads shelves
#   2. Scrape all your public friends' shelves
#   3. Enrich every unique book with cover, genres, page count, and top quotes
#
# The resulting SQLite database is the foundation for the ourshelf UI.
#
# Usage:
#   bash run.sh                                  # uses GOODREADS_USER_ID from .env
#   bash run.sh 204461698-other-user              # override for a one-off run
#   bash run.sh 204461698-other-user my.db        # custom db path (default: data/goodreads.db)
#
# Set GOODREADS_USER_ID in a .env file next to this script (see .env.example).
# .env is gitignored so it never gets pushed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Seconds to pause between scraping each friend's shelves.
# Increase this if you hit CAPTCHAs or empty results mid-run.
FRIEND_SCRAPE_DELAY="${FRIEND_SCRAPE_DELAY:-8}"

if [ -f "$SCRIPT_DIR/.env" ]; then
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/.env"
fi

if ! command -v uv &> /dev/null; then
    echo "uv not found — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Syncing dependencies..."
cd "$SCRIPT_DIR"
uv sync --quiet
uv run playwright install chromium --quiet

if [ ! -f "$SCRIPT_DIR/auth_state.json" ]; then
    echo
    echo "No saved Goodreads session found — logging in (one-time step)."
    echo "A browser window will open; log in, then come back here and press Enter."
    echo
    uv run python "$SCRIPT_DIR/src/goodreads_scraper.py" login
fi

USER_ID="${1:-${GOODREADS_USER_ID:-}}"
if [ -z "$USER_ID" ]; then
    read -rp "Goodreads user ID (e.g. 204461698-kyra-anum, from your profile URL): " USER_ID
fi

DB_PATH="${2:-$SCRIPT_DIR/data/goodreads.db}"
SCRAPER="uv run python $SCRIPT_DIR/src/goodreads_scraper.py"

# ── Step 1: your own shelves ────────────────────────────────────────────────
echo
echo "==> [1/3] Scraping your shelves (user: $USER_ID) ..."
$SCRAPER scrape --user-id "$USER_ID" --db "$DB_PATH"

# ── Step 2: friends' shelves ─────────────────────────────────────────────────
echo
echo "==> [2/3] Fetching your friend list ..."
FRIEND_IDS=()
while IFS= read -r line; do
    [[ -n "$line" ]] && FRIEND_IDS+=("$line")
done < <($SCRAPER friends --user-id "$USER_ID" 2>/dev/null)

if [ ${#FRIEND_IDS[@]} -eq 0 ]; then
    echo "No public friends found — skipping."
else
    echo "Found ${#FRIEND_IDS[@]} friends. Scraping their shelves ..."
    for i in "${!FRIEND_IDS[@]}"; do
        friend_id="${FRIEND_IDS[$i]}"
        echo "  -> $friend_id"
        $SCRAPER scrape --user-id "$friend_id" --db "$DB_PATH"
        if [ $i -lt $(( ${#FRIEND_IDS[@]} - 1 )) ]; then
            echo "     (waiting ${FRIEND_SCRAPE_DELAY}s before next friend...)"
            sleep "$FRIEND_SCRAPE_DELAY"
        fi
    done
fi

# ── Step 3: enrich all books with detail + quotes ────────────────────────────
echo
echo "==> [3/3] Enriching books with cover, genres, page count, and quotes ..."

# Load the committed cache first so we only scrape books that aren't in it yet
$SCRAPER cache-load --db "$DB_PATH" --cache "$SCRIPT_DIR/data/book_details_cache.json"

$SCRAPER details --db "$DB_PATH"

# Save new entries back to the cache and push to the repo
$SCRAPER cache-save --db "$DB_PATH" --cache "$SCRIPT_DIR/data/book_details_cache.json"

echo
cd "$SCRIPT_DIR"
if git diff --quiet data/book_details_cache.json 2>/dev/null; then
    echo "No new book details to push to cache."
else
    git add data/book_details_cache.json
    git commit -m "update book details cache"
    git push && echo "Cache pushed to repo." || echo "Push failed — run 'git push' manually."
fi

echo
echo "Done. Full ourshelf database written to $DB_PATH"

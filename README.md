# ourshelf

A community bookshelf — scrapes Goodreads data for you and your friends and turns it into a shared, social reading experience.

> Goodreads deprecated their public API in 2020. This project uses Playwright to scrape the Goodreads web UI using your saved session. Use responsibly, keep request rates low, and be aware this is against Goodreads' ToS.

---

## How it works

1. You log in to Goodreads once — the session is saved locally
2. The scraper pulls your shelves (read, currently reading, want to read) and your friends' public shelves
3. All books are deduplicated into a shared SQLite database
4. A second pass enriches each unique book with cover art, description, genres, page count, and top quotes from the book's individual Goodreads page
5. The resulting database is the foundation for the ourshelf UI

---

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install the Playwright browser
uv run playwright install chromium
```

Copy `.env.example` to `.env` and fill in your Goodreads user ID (the number in your profile URL):

```bash
cp .env.example .env
```

---

## Running

### Full pipeline (recommended)

```bash
bash run.sh
```

This runs all three steps in order:
1. Scrape your shelves
2. Scrape all public friends' shelves (with 8s pause between each)
3. Enrich every unique book with detail page data and push the cache to the repo

Keep your laptop awake during a full run:
```bash
caffeinate bash run.sh
```

### Individual commands

```bash
# Log in (one-time — opens a real browser window)
uv run python src/goodreads_scraper.py login

# Scrape a user's shelves
uv run python src/goodreads_scraper.py scrape --user-id 204461698-kyra-anum

# Get a user's friend IDs (one per line, debug output to stderr)
uv run python src/goodreads_scraper.py friends --user-id 204461698-kyra-anum

# Enrich all books with detail page data
uv run python src/goodreads_scraper.py details

# Load book detail cache from repo into local db (run before 'details')
uv run python src/goodreads_scraper.py cache-load

# Save local book detail data back to repo cache (run after 'details')
uv run python src/goodreads_scraper.py cache-save
```

---

## Environment variables

Set in `.env` (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `GOODREADS_USER_ID` | — | Your Goodreads user ID (required) |
| `MAX_BOOKS` | `0` (no limit) | Cap books scraped per user — set to `10` for test runs |
| `FRIEND_SCRAPE_DELAY` | `8` | Seconds to wait between scraping each friend's shelves |

The scraper also reads `.env` automatically, so env vars apply whether you run via `run.sh` or call the script directly.

---

## File layout

```
ourshelf/
├── src/
│   └── goodreads_scraper.py   # All scraping logic + CLI
├── debug/
│   ├── debug_shelf.py         # Diagnose shelf scraping issues
│   └── debug_friends.py       # Diagnose friend list scraping issues
├── data/
│   ├── goodreads.db           # Local SQLite database (gitignored)
│   └── book_details_cache.json  # Shared book detail cache (committed, no PII)
├── docs/
│   ├── brainstorm.md          # Project concept and design decisions
│   ├── schema.md              # Database schema with ER diagram
│   └── handoff/               # Session handoff notes
├── pyproject.toml             # Python project + dependencies
├── uv.lock                    # Locked dependency versions
├── run.sh                     # Full pipeline runner
└── .env                       # Local config (gitignored)
```

---

## Database schema

Four tables in `data/goodreads.db`:

- **`person`** — Goodreads users (you + friends): `goodreads_id`, `name`, `goodreads_url`, `avatar_url`
- **`book`** — Deduplicated books: `goodreads_book_id`, `title`, `author`
- **`person_book`** — Who shelved what: `person_id`, `book_id`, `shelf`, `rating`, `date_read`, `date_added`
- **`book_detail`** — Enriched metadata: `cover_url`, `description`, `genres` (JSON), `page_count`, `top_quotes` (JSON)

See `docs/schema.md` for the full ER diagram.

---

## Book detail cache

`data/book_details_cache.json` is committed to the repo and contains enriched book metadata with no PII (no user IDs, ratings, or shelf data — only book-level info). Before the `details` scrape runs, the pipeline loads this cache into the local db so only genuinely new books get scraped. After the run, new entries are saved back and pushed.

This means after the first full run, subsequent runs are much faster.

---

## Debugging

If the scraper returns 0 books, it saves the raw HTML to `debug/` for inspection:

```bash
# Run the shelf debug script to see what Goodreads actually served
uv run python debug/debug_shelf.py --user-id 204461698-kyra-anum

# Run the friends debug script
uv run python debug/debug_friends.py --user-id 204461698-kyra-anum
```

Open the generated `debug/debug_screenshot.png` to see what the headless browser saw.

# References & Lessons Learned

Notes on non-obvious decisions, gotchas we hit, and why things are the way they are.

---

## GitHub Pages deployment

**Problem: `gh-pages` npm package silently drops `index.html`**

When using the `gh-pages` npm package (`gh-pages -d dist`), it creates a temp clone of the repo and runs `git add` inside it. That clone inherits the project's `.gitignore`. If `.gitignore` has any HTML rule (even `*.html` scoped to a subdirectory), the package can silently exclude files — in our case, `index.html` was consistently dropped, leaving a `gh-pages` branch with only `assets/` and `favicon.svg`. The site 404'd because there was no `index.html`.

**Fix: deploy from an isolated temp repo**

`web/deploy.sh` initializes a brand-new git repo in a temp directory, copies `web/dist/` into it with `git add -f` (force-add bypasses all gitignores), and force-pushes to `origin gh-pages`. There is no shared gitignore, no inherited config — it always includes everything in `dist/`.

```bash
bash web/deploy.sh
```

The pre-push hook in `.githooks/pre-push` calls this script instead of `npm run deploy`.

**Key detail: `web/dist/` is gitignored on `main`**

`web/dist/` stays in `.gitignore` so built files are never committed to `main`. They only ever land on the `gh-pages` branch via the deploy script. This is intentional.

---

## Goodreads scraping

**No public API since 2020**

Goodreads deprecated their API in 2020 and does not offer a replacement. All data is scraped via Playwright (headless Chromium). Session auth is saved to `auth_state.json` after a one-time manual login — this file contains real session cookies and must stay gitignored.

**Rate limiting**

Goodreads will throttle or block requests if hit too fast. The scraper uses:
- `REQUEST_DELAY_SECONDS = 2.0` between shelf pages
- `DETAIL_REQUEST_DELAY_SECONDS = 3.0` between book detail pages
- `FRIEND_SCRAPE_DELAY` (env var, default 8s) between each friend's full scrape

For long runs, use `caffeinate bash run.sh` to prevent the laptop sleeping and killing the browser session.

**`per_page=100` on shelf URLs**

Goodreads defaults to 20 books per page. Appending `?per_page=100` to shelf URLs reduces the number of page requests by 5x. This matters for users with large shelves.

**Quotes page timeout handling**

The Goodreads quotes page (`/work/quotes/`) frequently times out. Rather than letting this crash the entire book detail scrape, `scrape_quotes()` is wrapped in a try/except that returns `[]` on any exception. The book is still saved with all other fields; quotes just come back empty and can be retried on the next run.

**`wait_until="domcontentloaded"` not `networkidle`**

Goodreads pages never reach `networkidle` (background requests keep firing). Using `networkidle` as the Playwright wait condition causes every page load to time out. Use `domcontentloaded`.

**`MAX_BOOKS` env var for test runs**

Set `MAX_BOOKS=10` in `.env` to cap how many books are scraped per user during development. The scraper uses a `done` flag that breaks out of both the shelf loop and the page loop — a plain `break` only exits the innermost loop and doesn't actually stop the scrape.

---

## Database

**Normalized 4-table schema**

The schema is intentionally normalized rather than flat:
- `book` holds deduplicated book records keyed on `goodreads_book_id` (extracted from the title link href)
- `person_book` is the junction table — shelf, rating, dates all live here per-person
- `book_detail` is enriched separately in a second pass, so the main scrape stays fast
- `person` stores name/avatar scraped from the profile page

This means the same book appears once in `book` even if 10 friends all shelved it, with 10 rows in `person_book`.

**Book detail cache (`data/book_details_cache.json`)**

After a full detail scrape, results are exported to `data/book_details_cache.json` and committed to the repo. Before the next detail scrape, this cache is loaded into the local db first — so only genuinely new books need to be scraped. This file contains only book-level metadata (no user IDs, ratings, or shelf data) and is safe to commit.

---

## Python / tooling

**`uv` for dependency management**

All Python is run via `uv run python ...`. This ensures the locked virtualenv from `uv.lock` is always used. `run.sh` auto-installs `uv` if it's not present.

**`.env` auto-loading**

The scraper calls `_load_env()` at module level, which reads `.env` from the project root before any code runs. This means env vars (`GOODREADS_USER_ID`, `MAX_BOOKS`, etc.) work whether you invoke the script directly or via `run.sh`.

**`mapfile` not available on macOS**

macOS ships bash 3.2, which does not have `mapfile`/`readarray`. Use `while IFS= read -r line; do ...; done < <(command)` instead.

---

## Git / repo

**`.githooks/` for version-controlled hooks**

Hooks live in `.githooks/` (not `.git/hooks/`) so they're committed to the repo and shared with collaborators. Activated once per clone with:
```bash
git config core.hooksPath .githooks
```

**What is and isn't gitignored**

| Path | Gitignored | Why |
|---|---|---|
| `auth_state.json` | yes | Goodreads session cookies |
| `data/goodreads.db` | yes | Contains PII (user IDs, reading history) |
| `.env` | yes | Contains user credentials |
| `web/dist/` | yes | Built output — deployed to gh-pages, not committed to main |
| `debug/*.html` | yes | Captured Goodreads HTML — can be large, not useful in history |
| `data/book_details_cache.json` | **no** | Book metadata only, no PII — shared across contributors |

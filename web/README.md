# ourshelf — web

The interactive digital library UI. Built with React + Vite + React Router
(`HashRouter`, so it works on GitHub Pages with no server-side routing).

## Pages

| Route | Page | What it shows |
|---|---|---|
| `/` | `GenresPage` | Stats scorecard, reader avatars, genre folders (staggered tabs, cascading left-to-right) |
| `/genre/:genre` | `ShelfPage` | Every tagged book whose primary genre or raw genre tags match `:genre`, as a row of spines |
| `/person/:id` | `ProfilePage` | One reader's ID card + every book they've marked `read` |
| `/people` | `PeoplePage` | Index of all readers, linking to their profiles |

A hamburger menu (top-left, present on every page) links to `/` and
`/people`.

Genre folders only include books that have been through detail enrichment
(i.e. have at least one genre tag) — most of the 937 scraped books haven't
been enriched yet (see `../docs/handoff/`), and dumping all of them into a
"Fiction" catch-all would bury the real genres. Untagged books still count
toward profile shelves and the stats scorecard, which read from the full
scrape regardless of enrichment status.

A book with nobody's `read` shelf entry (only `to-read`) renders greyed out
and dashed-bordered on the shelf, tagged "TBR", to distinguish it from books
someone has actually finished.

## Running locally

```bash
npm install
npm run dev
```

## Data

The app reads three generated JSON files under `src/data/`, all built by
`../scripts/export_books.py` from `../data/goodreads.db`:

| File | Contents |
|---|---|
| `books.json` | Every scraped book: title, author (`First Last`, flipped from Goodreads' `Last, First`), genres, `readBy`/`tbrBy` (arrays of `{id, name}` reader refs), and a derived `status` (`read` if anyone has finished it, else `tbr`) |
| `people.json` | Readers who have at least one shelf entry (the scraper leaves behind empty `person` rows with no books — those are filtered out), with read/TBR counts |
| `stats.json` | Aggregate KPIs for the homepage scorecard: unique books read, combined read count, overlap count/percent, top shared titles |

Whenever `data/goodreads.db` changes, regenerate all three from the repo
root:

```bash
uv run python scripts/export_books.py
```

There's a fourth, hand-authored data file, `src/data/readerCards.json` —
per-reader personality stats (favorite genre, reading medium, skim rate,
reading speed) shown on the ID card on each profile page. These aren't
derivable from the scrape, so they're maintained by hand, keyed by the same
reader `id` (slug) as `people.json`.

## Deploying to GitHub Pages

```bash
npm run build
npm run deploy
```

`deploy` pushes `dist/` to a `gh-pages` branch via the
[`gh-pages`](https://github.com/tschaub/gh-pages) package. Routing uses
`HashRouter` and `vite.config.js` sets `base: './'`, so the build works from
any project-page subpath without extra configuration.

### Auto-deploy on push

A `pre-push` git hook (tracked at `../.githooks/pre-push`) runs `npm run
build && npm run deploy` automatically whenever a push includes changes
under `web/` (`index.html`, `src/`, `public/`, `package.json`) — no manual
deploy step needed. It's already installed at `.git/hooks/pre-push` in this
checkout; git doesn't track `.git/hooks/`, so on a fresh clone reinstall it
with:

```bash
cp .githooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push
```

or point git at the tracked directory for every hook:

```bash
git config core.hooksPath .githooks
```

Heads up: once installed, this hook pushes to the `gh-pages` branch as a
side effect of an ordinary `git push` — no extra confirmation prompt.

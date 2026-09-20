"""
goodreads_scraper.py

Logs into Goodreads with Playwright, scrapes a user's "read",
"currently-reading", and "to-read" shelves, and writes the results
(title, author, rating, date read, date added) into a local SQLite database.

Setup:
    pip install playwright
    playwright install chromium

Usage:
    # First run: log in interactively (a real browser window opens so you
    # can handle any CAPTCHA/2FA), then save the session for future runs.
    python goodreads_scraper.py login

    # Scrape your own shelves
    python goodreads_scraper.py scrape --user-id YOUR_USER_ID --db goodreads.db

    # Scrape a friend's public shelves (numeric ID or vanity name from
    # their profile URL, e.g. goodreads.com/user/show/12345-jane-doe ->
    # user id "12345-jane-doe" or just "12345")
    python goodreads_scraper.py scrape --user-id 12345-jane-doe --db goodreads.db

Notes:
    - This uses Goodreads' web UI, not any official API (Goodreads retired
      its public developer API in 2020). It relies on the site's current
      HTML structure, so selectors may need updating if Goodreads changes
      their markup.
    - This is against Goodreads' Terms of Service. Use your own account,
      keep request rates low, and don't treat this as a stable long-term
      dependency.
    - Friends' shelves must be set to public for this to work without
      their login credentials.
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SRC_DIR = Path(__file__).parent
PROJECT_ROOT = SRC_DIR.parent

def _load_env():
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

_load_env()
STORAGE_STATE_PATH = PROJECT_ROOT / "auth_state.json"
DEBUG_DIR = PROJECT_ROOT / "debug"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "goodreads.db"
GOODREADS_LOGIN_URL = "https://www.goodreads.com/user/sign_in"
REQUEST_DELAY_SECONDS = 2.0       # delay between shelf list pages
DETAIL_REQUEST_DELAY_SECONDS = 3.0  # delay between individual book detail pages
SHELVES = ("read", "currently-reading", "to-read")


def login():
    """
    Opens a real (non-headless) browser so you can log in manually,
    including solving any CAPTCHA. Saves the authenticated session
    (cookies + local storage) to disk so future runs don't need to
    log in again.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(GOODREADS_LOGIN_URL)

        print("A browser window has opened.")
        print("Log into Goodreads manually (handle any CAPTCHA/2FA).")
        input("Once you're fully logged in and see your home feed, press Enter here...")

        context.storage_state(path=str(STORAGE_STATE_PATH))
        browser.close()
        print(f"Session saved to {STORAGE_STATE_PATH}")


def init_db(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS person (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goodreads_id TEXT UNIQUE,
            name TEXT,
            goodreads_url TEXT,
            avatar_url TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goodreads_book_id TEXT UNIQUE,
            title TEXT,
            author TEXT
        );

        CREATE TABLE IF NOT EXISTS book_detail (
            goodreads_book_id TEXT PRIMARY KEY,
            cover_url TEXT,
            description TEXT,
            genres TEXT,
            page_count INTEGER,
            top_quotes TEXT,
            detail_scraped_at TEXT
        );

        CREATE TABLE IF NOT EXISTS person_book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER REFERENCES person(id),
            book_id INTEGER REFERENCES book(id),
            shelf TEXT,
            rating INTEGER,
            date_read TEXT,
            date_added TEXT,
            synced_at TEXT,
            UNIQUE(person_id, book_id, shelf)
        );
        """
    )
    conn.commit()
    return conn


def parse_rating(row):
    """
    Goodreads renders a book's star rating as CSS classes, not text
    (e.g. <span class="p8"> inside .staticStars), so it can't be read
    with inner_text(). The class is "p" + N where N is the rating on a
    0-10 scale in half-star steps (p10 = 5 stars, p8 = 4 stars, etc).
    Returns an int 1-5, or None if the book is unrated.
    """
    star_span = row.query_selector("td.field.rating .staticStars span[class*='p']")
    if not star_span:
        return None
    class_attr = star_span.get_attribute("class") or ""
    match = re.search(r"\bp(\d+)\b", class_attr)
    if not match:
        return None
    rating = int(match.group(1)) // 2
    return rating if rating > 0 else None


def parse_book_id(row):
    """
    Extracts Goodreads' canonical book ID from the title link's href
    (e.g. /book/show/12345678-some-title -> "12345678"). This is the
    stable identifier to dedupe the same book across different users'
    shelves (see docs/schema.md: BOOK.goodreads_book_id).
    """
    link = row.query_selector("td.field.title a")
    href = link.get_attribute("href") if link else None
    match = re.search(r"/book/show/(\d+)", href or "")
    return match.group(1) if match else None


def parse_shelf_page(page, shelf):
    """
    Extracts book rows from a rendered Goodreads shelf/review-list page.
    Returns a list of dicts. Selectors target the classic table-based
    shelf layout (id="books"); adjust if Goodreads has changed markup.
    """
    rows = page.query_selector_all("tr.bookalike.review")
    books = []
    for row in rows:
        def text_of(selector):
            el = row.query_selector(selector)
            return el.inner_text().strip() if el else None

        title = text_of("td.field.title a")
        author = text_of("td.field.author a")
        goodreads_book_id = parse_book_id(row)
        rating = parse_rating(row)
        date_read = text_of("td.field.date_read .value")
        date_added = text_of("td.field.date_added .value")

        if title:
            books.append(
                {
                    "goodreads_book_id": goodreads_book_id,
                    "title": title,
                    "author": author,
                    "shelf": shelf,
                    "rating": rating,
                    "date_read": date_read,
                    "date_added": date_added,
                }
            )
    return books


def scrape_profile(page, user_id):
    """
    Visits a user's Goodreads profile page and returns their display name
    and avatar URL. Falls back to None for each if the selector doesn't match.
    Selectors target the current Goodreads profile layout.
    """
    url = f"https://www.goodreads.com/user/show/{user_id}"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1000)

    name_el = page.query_selector(".userProfileName") or page.query_selector("h1.userNameHeading")
    name = name_el.inner_text().strip() if name_el else None

    avatar_el = page.query_selector(".userProfilePhoto img") or page.query_selector(".leftAlignedProfilePicture img")
    avatar_url = avatar_el.get_attribute("src") if avatar_el else None

    return name, avatar_url


def upsert_person(conn, user_id, name=None, avatar_url=None):
    goodreads_url = f"https://www.goodreads.com/user/show/{user_id}"
    conn.execute(
        """
        INSERT INTO person (goodreads_id, name, goodreads_url, avatar_url, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(goodreads_id) DO UPDATE SET
            goodreads_url=excluded.goodreads_url,
            name=COALESCE(excluded.name, name),
            avatar_url=COALESCE(excluded.avatar_url, avatar_url)
        """,
        (user_id, name, goodreads_url, avatar_url, time.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    return conn.execute("SELECT id FROM person WHERE goodreads_id = ?", (user_id,)).fetchone()[0]


def upsert_book(conn, goodreads_book_id, title, author):
    conn.execute(
        """
        INSERT INTO book (goodreads_book_id, title, author)
        VALUES (?, ?, ?)
        ON CONFLICT(goodreads_book_id) DO UPDATE SET title=excluded.title, author=excluded.author
        """,
        (goodreads_book_id, title, author),
    )
    return conn.execute("SELECT id FROM book WHERE goodreads_book_id = ?", (goodreads_book_id,)).fetchone()[0]


def scrape_user(user_id, db_path, max_pages=50, max_books=None):
    """
    Scrapes a user's shelves and writes into person / book / person_book tables.
    Set max_books to stop early after N books — useful for test runs.
    """
    if not STORAGE_STATE_PATH.exists():
        print("No saved session found. Run `python goodreads_scraper.py login` first.")
        sys.exit(1)

    conn = init_db(db_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(STORAGE_STATE_PATH),
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        name, avatar_url = scrape_profile(page, user_id)
        person_id = upsert_person(conn, user_id, name=name, avatar_url=avatar_url)
        print(f"  Person: {name or '(name not found)'} (id={person_id})")
        time.sleep(REQUEST_DELAY_SECONDS)

        total_saved = 0
        skipped_no_id = 0
        done = False
        for shelf in SHELVES:
            if done:
                break
            for page_num in range(1, max_pages + 1):
                if max_books and total_saved >= max_books:
                    print(f"  [max_books={max_books}] limit reached — stopping early.")
                    done = True
                    break

                url = (
                    f"https://www.goodreads.com/review/list/{user_id}"
                    f"?shelf={shelf}&page={page_num}&per_page=100&print=true"
                )
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                try:
                    page.wait_for_selector("tr.bookalike.review", timeout=15000)
                except Exception:
                    pass
                page.wait_for_timeout(1000)

                shelf_books = parse_shelf_page(page, shelf)
                if not shelf_books:
                    if page_num == 1:
                        DEBUG_DIR.mkdir(exist_ok=True)
                        debug_path = DEBUG_DIR / f"debug_{user_id}_{shelf}.html"
                        debug_path.write_text(page.content(), encoding="utf-8")
                        print(f"  [warn] No books on {shelf} page 1 — saved HTML to {debug_path}")
                    break

                synced_at = time.strftime("%Y-%m-%d %H:%M:%S")
                for b in shelf_books:
                    if not b["goodreads_book_id"]:
                        skipped_no_id += 1
                        print(f"  [warn] Skipping '{b['title']}' — could not extract goodreads_book_id")
                        continue

                    book_id = upsert_book(conn, b["goodreads_book_id"], b["title"], b["author"])
                    conn.execute(
                        """
                        INSERT INTO person_book (person_id, book_id, shelf, rating, date_read, date_added, synced_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(person_id, book_id, shelf) DO UPDATE SET
                            rating=excluded.rating,
                            date_read=excluded.date_read,
                            date_added=excluded.date_added,
                            synced_at=excluded.synced_at
                        """,
                        (person_id, book_id, b["shelf"], b["rating"], b["date_read"], b["date_added"], synced_at),
                    )
                conn.commit()
                total_saved += len(shelf_books)
                print(f"  [{shelf}] page {page_num}: {len(shelf_books)} books (total: {total_saved})")
                time.sleep(REQUEST_DELAY_SECONDS)

        browser.close()

    conn.close()
    print(f"Done. {total_saved} rows saved for user {user_id} ({skipped_no_id} skipped — no book id).")


def parse_book_detail(page):
    """
    Scrapes enriched metadata from a book's Goodreads page (/book/show/<id>).
    Selectors target Goodreads' current React layout; may need updating if
    they change their markup.
    Returns a dict with cover_url, description, genres, page_count, and
    work_id (used to fetch quotes from /work/quotes/<work_id>).
    """
    cover_el = page.query_selector("[data-testid='coverImage']")
    cover_url = cover_el.get_attribute("src") if cover_el else None

    desc_el = page.query_selector("[data-testid='description']")
    description = desc_el.inner_text().strip() if desc_el else None

    genre_els = page.query_selector_all("[data-testid='genresList'] .Button__labelItem")
    genres = [el.inner_text().strip() for el in genre_els if el.inner_text().strip()]

    pages_el = page.query_selector("[data-testid='pagesFormat']")
    page_count = None
    if pages_el:
        match = re.search(r"(\d+)\s*page", pages_el.inner_text())
        if match:
            page_count = int(match.group(1))

    quotes_link = page.query_selector("a[href*='/work/quotes/']")
    work_id = None
    if quotes_link:
        href = quotes_link.get_attribute("href") or ""
        match = re.search(r"/work/quotes/(\d+)", href)
        if match:
            work_id = match.group(1)

    return {
        "cover_url": cover_url,
        "description": description,
        "genres": genres,
        "page_count": page_count,
        "work_id": work_id,
    }


def scrape_quotes(page, work_id, limit=5):
    """
    Scrapes the top quotes for a book from /work/quotes/<work_id>.
    Returns a list of up to `limit` quote strings, or [] if the page times out.
    """
    if not work_id:
        return []
    try:
        url = f"https://www.goodreads.com/work/quotes/{work_id}"
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1000)

        quote_els = page.query_selector_all(".quoteText")
        quotes = []
        for el in quote_els[:limit]:
            text = el.inner_text().strip()
            if text:
                quotes.append(text)
        return quotes
    except Exception as e:
        print(f"    [warn] Quotes page timed out for work {work_id} — skipping quotes ({e.__class__.__name__})")
        return []


def scrape_book_details(db_path, delay=DETAIL_REQUEST_DELAY_SECONDS):
    """
    For every unique book in the books table that doesn't yet have a
    book_detail row, visits its Goodreads page to scrape enriched data
    (cover, description, genres, page count) then fetches the top 5 quotes.
    Safe to re-run; already-enriched books are skipped.
    """
    if not STORAGE_STATE_PATH.exists():
        print("No saved session found. Run `python goodreads_scraper.py login` first.")
        sys.exit(1)

    conn = init_db(db_path)

    rows = conn.execute(
        """
        SELECT goodreads_book_id FROM book
        WHERE goodreads_book_id IS NOT NULL
          AND goodreads_book_id NOT IN (SELECT goodreads_book_id FROM book_detail)
        """
    ).fetchall()
    book_ids = [r[0] for r in rows]
    print(f"Found {len(book_ids)} books to enrich.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(STORAGE_STATE_PATH),
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        failed = []
        for i, book_id in enumerate(book_ids, 1):
            url = f"https://www.goodreads.com/book/show/{book_id}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1500)

                detail = parse_book_detail(page)
                work_id = detail.pop("work_id")
                quotes = scrape_quotes(page, work_id)

                conn.execute(
                    """
                    INSERT OR REPLACE INTO book_detail
                    (goodreads_book_id, cover_url, description, genres, page_count, top_quotes, detail_scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        book_id,
                        detail["cover_url"],
                        detail["description"],
                        json.dumps(detail["genres"]),
                        detail["page_count"],
                        json.dumps(quotes),
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                conn.commit()
                print(f"  [{i}/{len(book_ids)}] Enriched {book_id}")
            except Exception as e:
                print(f"  [{i}/{len(book_ids)}] SKIP {book_id} — {e}")
                failed.append(book_id)

            time.sleep(delay)

        browser.close()

    conn.close()
    print(f"Done. Enriched {len(book_ids) - len(failed)} books in {db_path}.")
    if failed:
        print(f"  {len(failed)} books skipped (will be retried on next run): {failed[:10]}{'...' if len(failed) > 10 else ''}")


DEFAULT_CACHE_PATH = PROJECT_ROOT / "data" / "book_details_cache.json"


def cache_load(db_path, cache_path=DEFAULT_CACHE_PATH):
    """
    Imports book_detail rows from the committed JSON cache into the local db.
    Only inserts rows not already present, so it's safe to run before every
    detail scrape — existing local data is never overwritten.
    """
    cache_path = Path(cache_path)
    if not cache_path.exists():
        print(f"No cache found at {cache_path} — nothing to load.")
        return

    with open(cache_path) as f:
        entries = json.load(f)

    conn = init_db(db_path)
    loaded = 0
    for entry in entries:
        existing = conn.execute(
            "SELECT 1 FROM book_detail WHERE goodreads_book_id = ?",
            (entry["goodreads_book_id"],),
        ).fetchone()
        if not existing:
            conn.execute(
                """
                INSERT INTO book_detail
                (goodreads_book_id, cover_url, description, genres, page_count, top_quotes, detail_scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["goodreads_book_id"],
                    entry.get("cover_url"),
                    entry.get("description"),
                    entry.get("genres"),
                    entry.get("page_count"),
                    entry.get("top_quotes"),
                    entry.get("detail_scraped_at"),
                ),
            )
            loaded += 1
    conn.commit()
    conn.close()
    print(f"Cache load: imported {loaded} new entries from {cache_path} ({len(entries) - loaded} already present).")


def cache_save(db_path, cache_path=DEFAULT_CACHE_PATH):
    """
    Exports all book_detail rows from the local db to the JSON cache file.
    Merge strategy: cache is the union of existing cache + any new local rows,
    so books scraped by different people accumulate over time.
    """
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(exist_ok=True)

    existing = {}
    if cache_path.exists():
        with open(cache_path) as f:
            for entry in json.load(f):
                existing[entry["goodreads_book_id"]] = entry

    conn = init_db(db_path)
    rows = conn.execute(
        "SELECT goodreads_book_id, cover_url, description, genres, page_count, top_quotes, detail_scraped_at FROM book_detail"
    ).fetchall()
    conn.close()

    new_count = 0
    for row in rows:
        book_id = row[0]
        if book_id not in existing:
            new_count += 1
        existing[book_id] = {
            "goodreads_book_id": row[0],
            "cover_url": row[1],
            "description": row[2],
            "genres": row[3],
            "page_count": row[4],
            "top_quotes": row[5],
            "detail_scraped_at": row[6],
        }

    with open(cache_path, "w") as f:
        json.dump(sorted(existing.values(), key=lambda x: x["goodreads_book_id"]), f, indent=2)

    print(f"Cache save: {new_count} new entries added, {len(existing)} total in {cache_path}.")


def get_friend_ids(user_id):
    """
    Scrapes a user's friends list and returns their user IDs, so you can
    loop scrape_user() over each one for a shared bookshelf site.
    """
    if not STORAGE_STATE_PATH.exists():
        print("No saved session found. Run `python goodreads_scraper.py login` first.")
        sys.exit(1)

    friend_ids = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(STORAGE_STATE_PATH),
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        page_num = 1
        while True:
            url = f"https://www.goodreads.com/friend/user/{user_id}?page={page_num}"
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_selector('a[rel="acquaintance"]', timeout=15000)
            except Exception:
                pass  # no friends on this page (or none at all) — fall through and check below
            page.wait_for_timeout(1000)

            links = page.query_selector_all('a[rel="acquaintance"]')
            found_any = False
            for link in links:
                href = link.get_attribute("href") or ""
                match = re.search(r"/user/show/(\d+[\w-]*)", href)
                if match:
                    friend_ids.append(match.group(1))
                    found_any = True
                else:
                    print(f"  (unmatched href: {href!r})", file=sys.stderr)

            print(f"Page {page_num}: {len(links)} elements found, {sum(1 for l in links if l)} processed", file=sys.stderr)

            if not found_any:
                break
            page_num += 1
            time.sleep(REQUEST_DELAY_SECONDS)

        browser.close()

    friend_ids = sorted(set(friend_ids))
    print(f"Found {len(friend_ids)} friends.", file=sys.stderr)
    for fid in friend_ids:
        print(fid)
    return friend_ids


def main():
    parser = argparse.ArgumentParser(description="Goodreads login + scraper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("login", help="Interactively log in and save session")

    scrape_parser = subparsers.add_parser(
        "scrape", help="Scrape a user's read, currently-reading, and to-read shelves"
    )
    scrape_parser.add_argument("--user-id", required=True, help="Goodreads user ID or vanity URL slug")
    scrape_parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite database")
    scrape_parser.add_argument(
        "--max-books",
        type=int,
        default=int(os.environ.get("MAX_BOOKS", 0)) or None,
        help="Stop after this many books per user (default: no limit; set MAX_BOOKS env var or pass here)",
    )

    friends_parser = subparsers.add_parser("friends", help="List a user's friend IDs")
    friends_parser.add_argument("--user-id", required=True, help="Goodreads user ID or vanity URL slug")

    details_parser = subparsers.add_parser(
        "details", help="Enrich all scraped books with cover, genres, page count, and top quotes"
    )
    details_parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite database")
    details_parser.add_argument(
        "--delay",
        type=float,
        default=DETAIL_REQUEST_DELAY_SECONDS,
        help=f"Seconds to wait between book detail page requests (default: {DETAIL_REQUEST_DELAY_SECONDS})",
    )

    cache_load_parser = subparsers.add_parser(
        "cache-load", help="Import book_detail cache from repo into local db (run before 'details')"
    )
    cache_load_parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite database")
    cache_load_parser.add_argument("--cache", default=str(DEFAULT_CACHE_PATH), help="Path to cache JSON file")

    cache_save_parser = subparsers.add_parser(
        "cache-save", help="Export book_detail from local db into repo cache (run after 'details')"
    )
    cache_save_parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite database")
    cache_save_parser.add_argument("--cache", default=str(DEFAULT_CACHE_PATH), help="Path to cache JSON file")

    args = parser.parse_args()

    if args.command == "login":
        login()
    elif args.command == "scrape":
        scrape_user(args.user_id, args.db, max_books=args.max_books)
    elif args.command == "friends":
        get_friend_ids(args.user_id)
    elif args.command == "details":
        scrape_book_details(args.db, delay=args.delay)
    elif args.command == "cache-load":
        cache_load(args.db, args.cache)
    elif args.command == "cache-save":
        cache_save(args.db, args.cache)


if __name__ == "__main__":
    main()
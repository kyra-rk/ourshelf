"""
goodreads_scraper.py

Logs into Goodreads with Playwright, scrapes a user's "shelves" (their book
list), and writes the results into a local SQLite database.

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
import re
import sqlite3
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

STORAGE_STATE_PATH = Path("auth_state.json")
GOODREADS_LOGIN_URL = "https://www.goodreads.com/user/sign_in"
REQUEST_DELAY_SECONDS = 2.0  # be polite; don't hammer the site


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
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            user_id TEXT,
            title TEXT,
            author TEXT,
            shelf TEXT,
            rating TEXT,
            date_read TEXT,
            date_added TEXT,
            scraped_at TEXT,
            PRIMARY KEY (user_id, title, author, shelf)
        )
        """
    )
    conn.commit()
    return conn


def parse_shelf_page(page):
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
        shelf = text_of("td.field.shelves .value")
        rating = text_of("td.field.rating .value")
        date_read = text_of("td.field.date_read .value")
        date_added = text_of("td.field.date_added .value")

        if title:
            books.append(
                {
                    "title": title,
                    "author": author,
                    "shelf": shelf,
                    "rating": rating,
                    "date_read": date_read,
                    "date_added": date_added,
                }
            )
    return books


def scrape_user(user_id, db_path, shelf="read", max_pages=50):
    """
    Scrapes a user's shelf (default "read"; also try "currently-reading",
    "to-read", or "" for all shelves) and writes results to SQLite.
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

        total_saved = 0
        for page_num in range(1, max_pages + 1):
            url = (
                f"https://www.goodreads.com/review/list/{user_id}"
                f"?shelf={shelf}&page={page_num}&print=true"
            )
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_selector("tr.bookalike.review", timeout=15000)
            except Exception:
                pass  # shelf may genuinely be empty — fall through and check below
            page.wait_for_timeout(1000)  # let the table render

            books = parse_shelf_page(page)
            if not books:
                break  # no more pages

            scraped_at = time.strftime("%Y-%m-%d %H:%M:%S")
            for b in books:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO books
                    (user_id, title, author, shelf, rating, date_read, date_added, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        b["title"],
                        b["author"],
                        b["shelf"],
                        b["rating"],
                        b["date_read"],
                        b["date_added"],
                        scraped_at,
                    ),
                )
            conn.commit()
            total_saved += len(books)
            print(f"Page {page_num}: saved {len(books)} books (running total: {total_saved})")

            time.sleep(REQUEST_DELAY_SECONDS)

        browser.close()

    conn.close()
    print(f"Done. {total_saved} books saved to {db_path} for user {user_id}.")


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
                    print(f"  (unmatched href: {href!r})")

            print(f"Page {page_num}: {len(links)} elements found, {sum(1 for l in links if l)} processed")

            if not found_any:
                break
            page_num += 1
            time.sleep(REQUEST_DELAY_SECONDS)

        browser.close()

    friend_ids = sorted(set(friend_ids))
    print(f"Found {len(friend_ids)} friends.")
    return friend_ids


def main():
    parser = argparse.ArgumentParser(description="Goodreads login + scraper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("login", help="Interactively log in and save session")

    scrape_parser = subparsers.add_parser("scrape", help="Scrape a user's shelf")
    scrape_parser.add_argument("--user-id", required=True, help="Goodreads user ID or vanity URL slug")
    scrape_parser.add_argument("--db", default="goodreads.db", help="Path to SQLite database")
    scrape_parser.add_argument("--shelf", default="read", help="Shelf to scrape (read, to-read, currently-reading, or empty for all)")

    friends_parser = subparsers.add_parser("friends", help="List a user's friend IDs")
    friends_parser.add_argument("--user-id", required=True, help="Goodreads user ID or vanity URL slug")

    args = parser.parse_args()

    if args.command == "login":
        login()
    elif args.command == "scrape":
        scrape_user(args.user_id, args.db, shelf=args.shelf)
    elif args.command == "friends":
        get_friend_ids(args.user_id)


if __name__ == "__main__":
    main()
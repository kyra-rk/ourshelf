"""
debug_shelf.py

Diagnostic helper: loads your saved session, navigates to your shelf page,
and saves a screenshot + the raw HTML so we can see what actually rendered
(are you logged in? does the table exist? has Goodreads changed markup?).

Usage:
    python3 debug_shelf.py --user-id 204461698-kyra-anum
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

STORAGE_STATE_PATH = Path("auth_state.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--shelf", default="read")
    args = parser.parse_args()

    if not STORAGE_STATE_PATH.exists():
        print("No auth_state.json found — run the login command first.")
        return

    url = f"https://www.goodreads.com/review/list/{args.user_id}?shelf={args.shelf}&print=true"

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

        page.on("console", lambda msg: print("CONSOLE:", msg.type, msg.text))
        page.on("requestfailed", lambda req: print("REQUEST FAILED:", req.url, req.failure))

        response = page.goto(url, wait_until="networkidle", timeout=30000)

        print("Response status:", response.status if response else None)
        print("Response headers:", dict(response.headers) if response else None)

        page.wait_for_timeout(2500)

        print("Final URL after navigation:", page.url)
        print("Page title:", page.title())

        page.screenshot(path="debug_screenshot.png", full_page=True)
        Path("debug_page.html").write_text(page.content(), encoding="utf-8")

        # quick sanity checks
        table_rows = page.query_selector_all("tr.bookalike.review")
        any_table = page.query_selector("table#books")
        sign_in_link = page.query_selector("a[href*='sign_in']")

        print(f"Rows matching 'tr.bookalike.review': {len(table_rows)}")
        print(f"Found table#books: {any_table is not None}")
        print(f"Found a 'sign in' link on page: {sign_in_link is not None}")

        browser.close()

    print("\nSaved debug_screenshot.png and debug_page.html in the current directory.")
    print("Open debug_screenshot.png to see what the scraper actually saw.")


if __name__ == "__main__":
    main()
"""
debug_friends.py

Diagnostic helper for the friends list, same idea as debug_shelf.py.

Usage:
    python3 debug_friends.py --user-id 204461698-kyra-anum
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

STORAGE_STATE_PATH = Path("auth_state.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    args = parser.parse_args()

    if not STORAGE_STATE_PATH.exists():
        print("No auth_state.json found — run the login command first.")
        return

    url = f"https://www.goodreads.com/friend/user/{args.user_id}?page=1"

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
        response = page.goto(url, wait_until="domcontentloaded", timeout=30000)

        print("Response status:", response.status if response else None)
        print("Final URL:", page.url)
        print("Page title:", page.title())

        page.wait_for_timeout(2000)

        user_links = page.query_selector_all('a[rel="acquaintance"]')
        print(f"Found {len(user_links)} a[rel='acquaintance'] elements")

        page.screenshot(path="debug_friends_screenshot.png", full_page=True)
        Path("debug_friends_page.html").write_text(page.content(), encoding="utf-8")

        browser.close()

    print("\nSaved debug_friends_screenshot.png and debug_friends_page.html")


if __name__ == "__main__":
    main()
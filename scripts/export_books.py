"""Export book + book_detail rows into a static JSON file for the React UI.

The site is a static gh-pages build, so it can't query SQLite directly —
this script is the bridge: run it whenever data/goodreads.db changes to
refresh web/src/data/books.json.

Usage: uv run python scripts/export_books.py
"""

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "goodreads.db"
OUT_PATH = ROOT / "web" / "src" / "data" / "books.json"

# Ordered priority list for bucketing a book into a single primary genre.
# Goodreads gives each book a list of genre tags (most to least relevant);
# we walk this list in order and the first tag that matches wins. This
# keeps folder counts reasonable instead of exploding into one folder per
# raw tag combination.
GENRE_PRIORITY = [
    "Nonfiction",
    "Classics",
    "Historical Fiction",
    "Graphic Novels",
    "Mystery",
    "Dystopia",
    "Science Fiction",
    "Fantasy",
    "Middle Grade",
    "Childrens",
]
FALLBACK_GENRE = "Fiction"


def primary_genre(genres: list[str]) -> str:
    for candidate in GENRE_PRIORITY:
        if candidate in genres:
            return candidate
    return FALLBACK_GENRE


def display_name(name: str, goodreads_id: str) -> str:
    """Person.name is blank for some scraped profiles (see docs/handoff) —
    fall back to a title-cased version of the goodreads_id slug so readers
    still show up with a readable name instead of disappearing."""
    if name:
        return name
    parts = [p for p in goodreads_id.split("-") if not p.isdigit()]
    return " ".join(p.capitalize() for p in parts) or goodreads_id


def main() -> None:
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        """
        SELECT b.goodreads_book_id, b.title, b.author,
               bd.cover_url, bd.description, bd.genres, bd.page_count
        FROM book b
        JOIN book_detail bd ON b.goodreads_book_id = bd.goodreads_book_id
        ORDER BY b.title
        """
    ).fetchall()

    reader_rows = con.execute(
        """
        SELECT b.goodreads_book_id, p.name, p.goodreads_id
        FROM person_book pb
        JOIN person p ON p.id = pb.person_id
        JOIN book b ON b.id = pb.book_id
        WHERE pb.shelf = 'read'
        """
    ).fetchall()
    con.close()

    readers_by_book: dict[str, list[str]] = {}
    for goodreads_book_id, name, goodreads_id in reader_rows:
        reader = display_name(name, goodreads_id)
        readers_by_book.setdefault(goodreads_book_id, [])
        if reader not in readers_by_book[goodreads_book_id]:
            readers_by_book[goodreads_book_id].append(reader)

    books = []
    for goodreads_book_id, title, author, cover_url, description, genres_json, page_count in rows:
        genres = json.loads(genres_json) if genres_json else []
        books.append(
            {
                "id": goodreads_book_id,
                "title": title,
                "author": author,
                "coverUrl": cover_url or None,
                "description": description,
                "genres": genres,
                "primaryGenre": primary_genre(genres),
                "pageCount": page_count,
                "readBy": sorted(readers_by_book.get(goodreads_book_id, [])),
            }
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(books, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(books)} books to {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

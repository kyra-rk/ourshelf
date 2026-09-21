"""Export book + book_detail rows into static JSON files for the React UI.

The site is a static gh-pages build, so it can't query SQLite directly —
this script is the bridge: run it whenever data/goodreads.db changes to
refresh web/src/data/*.json.

Usage: uv run python scripts/export_books.py
"""

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "goodreads.db"
BOOKS_OUT = ROOT / "web" / "src" / "data" / "books.json"
PEOPLE_OUT = ROOT / "web" / "src" / "data" / "people.json"
STATS_OUT = ROOT / "web" / "src" / "data" / "stats.json"

# Ordered priority list for bucketing a book into a single primary genre.
# Goodreads gives each book a list of genre tags (most to least relevant);
# we walk this list in order and the first tag that matches wins. This
# keeps folder counts reasonable instead of exploding into one folder per
# raw tag combination. Books with no genre data (not yet enriched) fall
# back to "Fiction" below.
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


def display_name(name: str | None, goodreads_id: str) -> str:
    """Person.name is blank for some scraped profiles (see docs/handoff) —
    fall back to a title-cased version of the goodreads_id slug so readers
    still show up with a readable name instead of disappearing."""
    if name:
        return name
    parts = [p for p in goodreads_id.split("-") if not p.isdigit()]
    return " ".join(p.capitalize() for p in parts) or goodreads_id


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "reader"


def format_author(author: str) -> str:
    """Goodreads lists authors as 'Last, First' — flip to 'First Last' for
    display. Names without a comma (mononyms, already-flipped entries) are
    left untouched."""
    if not author or "," not in author:
        return author
    last, _, first = author.partition(",")
    last, first = last.strip(), first.strip()
    if not last or not first:
        return author
    return f"{first} {last}"


def main() -> None:
    con = sqlite3.connect(DB_PATH)

    # Only people who actually have shelf activity — the scraper leaves
    # behind empty person rows (e.g. a shared login with zero person_book
    # rows) that shouldn't show up as "friends" in the UI.
    people_rows = con.execute(
        """
        SELECT p.id, p.name, p.goodreads_id, p.avatar_url
        FROM person p
        WHERE EXISTS (SELECT 1 FROM person_book pb WHERE pb.person_id = p.id)
        """
    ).fetchall()

    people = {}
    slugs_used = set()
    for person_id, name, goodreads_id, avatar_url in people_rows:
        display = display_name(name, goodreads_id)
        slug = slugify(display)
        while slug in slugs_used:
            slug += "-2"
        slugs_used.add(slug)
        people[person_id] = {"slug": slug, "name": display, "avatarUrl": avatar_url}

    book_rows = con.execute(
        """
        SELECT b.goodreads_book_id, b.title, b.author,
               bd.cover_url, bd.description, bd.genres, bd.page_count
        FROM book b
        LEFT JOIN book_detail bd ON b.goodreads_book_id = bd.goodreads_book_id
        ORDER BY b.title
        """
    ).fetchall()

    shelf_rows = con.execute(
        """
        SELECT b.goodreads_book_id, pb.person_id, pb.shelf
        FROM person_book pb
        JOIN book b ON b.id = pb.book_id
        WHERE pb.shelf IN ('read', 'to-read')
        """
    ).fetchall()

    readers_by_book: dict[str, list[int]] = {}
    tbr_by_book: dict[str, list[int]] = {}
    for goodreads_book_id, person_id, shelf in shelf_rows:
        if person_id not in people:
            continue
        bucket = readers_by_book if shelf == "read" else tbr_by_book
        bucket.setdefault(goodreads_book_id, [])
        if person_id not in bucket[goodreads_book_id]:
            bucket[goodreads_book_id].append(person_id)

    def people_refs(person_ids: list[int]) -> list[dict]:
        refs = [{"id": people[pid]["slug"], "name": people[pid]["name"]} for pid in person_ids]
        return sorted(refs, key=lambda r: r["name"])

    books = []
    for goodreads_book_id, title, author, cover_url, description, genres_json, page_count in book_rows:
        genres = json.loads(genres_json) if genres_json else []
        read_by = people_refs(readers_by_book.get(goodreads_book_id, []))
        tbr_by = people_refs(
            [pid for pid in tbr_by_book.get(goodreads_book_id, []) if pid not in readers_by_book.get(goodreads_book_id, [])]
        )
        books.append(
            {
                "id": goodreads_book_id,
                "title": title,
                "author": format_author(author),
                "coverUrl": cover_url or None,
                "description": description,
                "genres": genres,
                "primaryGenre": primary_genre(genres),
                "pageCount": page_count,
                "readBy": read_by,
                "tbrBy": tbr_by,
                "status": "read" if read_by else "tbr",
            }
        )

    # ---- people.json ----
    people_out = []
    for person_id, info in people.items():
        read_count = sum(1 for readers in readers_by_book.values() if person_id in readers)
        tbr_count = sum(1 for readers in tbr_by_book.values() if person_id in readers)
        people_out.append(
            {
                "id": info["slug"],
                "name": info["name"],
                "avatarUrl": info["avatarUrl"],
                "readCount": read_count,
                "tbrCount": tbr_count,
            }
        )
    people_out.sort(key=lambda p: -p["readCount"])

    # ---- stats.json ----
    total_unique_read = len(readers_by_book)
    total_unique_tbr = len(tbr_by_book)
    total_read_instances = sum(len(v) for v in readers_by_book.values())
    overlap_book_ids = [bid for bid, readers in readers_by_book.items() if len(readers) >= 2]
    overlap_count = len(overlap_book_ids)
    overlap_percent = round((overlap_count / total_unique_read) * 100, 1) if total_unique_read else 0.0

    title_by_id = {row[0]: (row[1], row[2]) for row in book_rows}
    shared_books = sorted(
        (
            {
                "id": bid,
                "title": title_by_id[bid][0],
                "author": format_author(title_by_id[bid][1]),
                "readByCount": len(readers_by_book[bid]),
            }
            for bid in overlap_book_ids
            if bid in title_by_id
        ),
        key=lambda b: (-b["readByCount"], b["title"]),
    )[:5]

    stats = {
        "totalPeople": len(people_out),
        "totalUniqueBooksRead": total_unique_read,
        "totalReadInstances": total_read_instances,
        "totalUniqueBooksTbr": total_unique_tbr,
        "overlapBooks": overlap_count,
        "overlapPercent": overlap_percent,
        "topSharedBooks": shared_books,
        "perPerson": [{"name": p["name"], "readCount": p["readCount"], "tbrCount": p["tbrCount"]} for p in people_out],
    }

    con.close()

    for path, payload in ((BOOKS_OUT, books), (PEOPLE_OUT, people_out), (STATS_OUT, stats)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

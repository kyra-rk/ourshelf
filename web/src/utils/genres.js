import books from '../data/books.json'
import { SPINE_COLORS } from './palette.js'

// Mirrors GENRE_PRIORITY in scripts/export_books.py, purely for a stable
// display order on the folders page (biggest thematic groups don't get
// shuffled around between reloads).
const GENRE_ORDER = [
  'Fantasy',
  'Dystopia',
  'Science Fiction',
  'Classics',
  'Historical Fiction',
  'Mystery',
  'Graphic Novels',
  'Nonfiction',
  'Middle Grade',
  'Childrens',
  'Fiction',
]

// Most of the 937 scraped books haven't been through detail enrichment yet
// (see docs/handoff) and so have no genre tags at all — lumping all of
// those into a fallback "Fiction" folder would bury the real genres under
// hundreds of untagged books. Genre browsing only considers books that
// actually have genre data; untagged books still show up on profile pages
// and in stats, just not sorted into a folder yet.
function taggedBooks() {
  return books.filter((book) => book.genres.length > 0)
}

export function getGenreFolders() {
  const counts = new Map()
  for (const book of taggedBooks()) {
    counts.set(book.primaryGenre, (counts.get(book.primaryGenre) || 0) + 1)
  }

  const known = GENRE_ORDER.filter((genre) => counts.has(genre))
  const extra = [...counts.keys()].filter((genre) => !GENRE_ORDER.includes(genre))

  return [...known, ...extra].map((genre) => ({
    genre,
    count: counts.get(genre),
  }))
}

// Genre chips in the book detail card show every raw tag Goodreads gave a
// book (not just its primaryGenre bucket), so browsing by one has to match
// against the full tag list — otherwise clicking e.g. "Magic" on a book
// bucketed under Fantasy would land on an empty shelf.
export function getBooksForGenre(genre) {
  return taggedBooks().filter((book) => book.primaryGenre === genre || book.genres.includes(genre))
}

// Stable color per genre folder, shared between the homepage folder grid
// and the shelf page's folder-tab header so a genre reads as the same
// "folder" wherever it shows up.
const FOLDER_ORDER = getGenreFolders().map((folder) => folder.genre)

export function getGenreColor(genre) {
  const index = FOLDER_ORDER.indexOf(genre)
  return SPINE_COLORS[(index < 0 ? 0 : index) % SPINE_COLORS.length]
}

export function getBookById(id) {
  return books.find((book) => book.id === id)
}

export function getReadBooksForPerson(personId) {
  return books
    .filter((book) => book.readBy.some((reader) => reader.id === personId))
    .sort((a, b) => a.title.localeCompare(b.title))
}

import books from '../data/books.json'

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

export function getGenreFolders() {
  const counts = new Map()
  for (const book of books) {
    counts.set(book.primaryGenre, (counts.get(book.primaryGenre) || 0) + 1)
  }

  const known = GENRE_ORDER.filter((genre) => counts.has(genre))
  const extra = [...counts.keys()].filter((genre) => !GENRE_ORDER.includes(genre))

  return [...known, ...extra].map((genre) => ({
    genre,
    count: counts.get(genre),
  }))
}

export function getBooksForGenre(genre) {
  return books.filter((book) => book.primaryGenre === genre)
}

export function getBookById(id) {
  return books.find((book) => book.id === id)
}

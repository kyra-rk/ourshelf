import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import BookDetail from '../components/BookDetail.jsx'
import BookSpine from '../components/BookSpine.jsx'
import { getBooksForGenre, getGenreColor } from '../utils/genres.js'
import { textColorFor } from '../utils/palette.js'

function ShelfPage() {
  const { genre } = useParams()
  const decodedGenre = decodeURIComponent(genre)
  const books = getBooksForGenre(decodedGenre)
  const [selectedBook, setSelectedBook] = useState(null)
  const color = getGenreColor(decodedGenre)
  const textColor = textColorFor(color)

  return (
    <main className="shelf-page">
      <div className="shelf-folder-tab" style={{ '--folder-color': color, color: textColor }}>
        <Link to="/" className="back-button">
          ← genres
        </Link>
        <h1>{decodedGenre}</h1>
      </div>
      <div className="shelf-folder-body" style={{ '--folder-color': color }} />

      {books.length > 0 ? (
        <div className="shelf-row">
          {books.map((book) => (
            <BookSpine key={book.id} book={book} onSelect={setSelectedBook} />
          ))}
        </div>
      ) : (
        <p className="empty-shelf">No books on this shelf yet.</p>
      )}

      <BookDetail book={selectedBook} onClose={() => setSelectedBook(null)} />
    </main>
  )
}

export default ShelfPage

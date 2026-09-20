import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import BookDetail from '../components/BookDetail.jsx'
import BookSpine from '../components/BookSpine.jsx'
import { getBooksForGenre } from '../utils/genres.js'

function ShelfPage() {
  const { genre } = useParams()
  const decodedGenre = decodeURIComponent(genre)
  const books = getBooksForGenre(decodedGenre)
  const [selectedBook, setSelectedBook] = useState(null)

  return (
    <main className="shelf-page">
      <header className="shelf-header">
        <Link to="/" className="back-button">
          ← genres
        </Link>
        <h1>{decodedGenre}</h1>
      </header>

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

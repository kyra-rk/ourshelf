import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import BookDetail from '../components/BookDetail.jsx'
import BookSpine from '../components/BookSpine.jsx'
import ReaderIdCard from '../components/ReaderIdCard.jsx'
import { getPersonById } from '../utils/people.js'
import { getReadBooksForPerson } from '../utils/genres.js'

function ProfilePage() {
  const { id } = useParams()
  const person = getPersonById(id)
  const books = person ? getReadBooksForPerson(id) : []
  const [selectedBook, setSelectedBook] = useState(null)

  if (!person) {
    return (
      <main className="shelf-page">
        <header className="shelf-header">
          <Link to="/" className="back-button">
            ← ourshelf
          </Link>
          <h1>reader not found</h1>
        </header>
      </main>
    )
  }

  return (
    <main className="shelf-page">
      <header className="shelf-header">
        <Link to="/" className="back-button">
          ← ourshelf
        </Link>
        <h1>{person.name}&rsquo;s shelf</h1>
        <span className="profile-subcount">{books.length} books read</span>
      </header>

      <ReaderIdCard person={person} />

      {books.length > 0 ? (
        <div className="shelf-row">
          {books.map((book) => (
            <BookSpine key={book.id} book={book} onSelect={setSelectedBook} />
          ))}
        </div>
      ) : (
        <p className="empty-shelf">No finished books yet.</p>
      )}

      <BookDetail book={selectedBook} onClose={() => setSelectedBook(null)} />
    </main>
  )
}

export default ProfilePage

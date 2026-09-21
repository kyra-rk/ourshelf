import { Link } from 'react-router-dom'

function BookDetail({ book, onClose }) {
  if (!book) return null

  return (
    <div className="book-detail-overlay" onClick={onClose}>
      <div className="book-detail-card" onClick={(event) => event.stopPropagation()}>
        <button type="button" className="detail-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <h2>{book.title}</h2>
        <p className="detail-author">{book.author}</p>
        {book.genres.length > 0 ? (
          <div className="detail-genres">
            {book.genres
              .filter((genre) => genre !== '...more')
              .map((genre) => (
                <Link key={genre} to={`/genre/${encodeURIComponent(genre)}`} className="genre-chip">
                  {genre}
                </Link>
              ))}
          </div>
        ) : null}
        {book.pageCount ? <p className="detail-pages">{book.pageCount} pages</p> : null}
        <div className="detail-readers">
          <span className="detail-readers-label">Read by</span>
          {book.readBy.length > 0 ? (
            <div className="detail-genres">
              {book.readBy.map((reader) => (
                <Link key={reader.id} to={`/person/${reader.id}`} className="reader-chip">
                  {reader.name}
                </Link>
              ))}
            </div>
          ) : (
            <span className="detail-readers-empty">nobody on ourshelf yet</span>
          )}
        </div>
        {book.tbrBy.length > 0 ? (
          <div className="detail-readers">
            <span className="detail-readers-label">Want to read</span>
            <div className="detail-genres">
              {book.tbrBy.map((reader) => (
                <Link key={reader.id} to={`/person/${reader.id}`} className="reader-chip reader-chip--tbr">
                  {reader.name}
                </Link>
              ))}
            </div>
          </div>
        ) : null}
        {book.description ? (
          <p className="detail-description">{book.description}</p>
        ) : (
          <p className="detail-description detail-description--empty">No description available.</p>
        )}
      </div>
    </div>
  )
}

export default BookDetail

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
        <div className="detail-genres">
          {book.genres.map((genre) => (
            <span key={genre} className="genre-chip">
              {genre}
            </span>
          ))}
        </div>
        {book.pageCount ? <p className="detail-pages">{book.pageCount} pages</p> : null}
        <div className="detail-readers">
          <span className="detail-readers-label">Read by</span>
          {book.readBy.length > 0 ? (
            <div className="detail-genres">
              {book.readBy.map((reader) => (
                <span key={reader} className="reader-chip">
                  {reader}
                </span>
              ))}
            </div>
          ) : (
            <span className="detail-readers-empty">nobody on ourshelf yet</span>
          )}
        </div>
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

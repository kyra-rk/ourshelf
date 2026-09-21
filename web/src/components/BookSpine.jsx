import { spineColorFor, textColorFor } from '../utils/palette.js'

// Deterministic per-book height variance so the row reads like a real
// shelf (books of slightly different sizes), not a uniform grid.
function heightFor(id) {
  let hash = 0
  const str = String(id)
  for (let i = 0; i < str.length; i += 1) {
    hash = (hash << 5) - hash + str.charCodeAt(i)
    hash |= 0
  }
  return 240 + (Math.abs(hash) % 60) // 240–300px
}

// Title text is vertical (writing-mode: vertical-rl), so a long title wraps
// into extra columns rather than getting truncated (see .spine-title) —
// the spine has to be wide enough to hold all of them, or the wrapped
// columns spill into the neighboring spine. Estimate columns needed from
// character count and the vertical room a column actually has.
function widthFor(title, author, height) {
  const titleAreaHeight = height * 0.6
  const authorAreaHeight = height * 0.26
  const titleColumns = Math.max(1, Math.ceil((title.length * 15) / titleAreaHeight))
  const authorColumns = Math.max(1, Math.ceil((author.length * 12) / authorAreaHeight))
  const width = Math.max(titleColumns * 22, authorColumns * 18) + 16
  return Math.min(150, Math.max(46, Math.round(width)))
}

function BookSpine({ book, onSelect }) {
  const color = spineColorFor(book.id)
  const textColor = textColorFor(color)
  const height = heightFor(book.id)
  const width = widthFor(book.title, book.author, height)
  const isTbr = book.status === 'tbr'

  return (
    <button
      type="button"
      className={`book-spine${isTbr ? ' book-spine--tbr' : ''}`}
      style={{
        '--spine-color': color,
        color: textColor,
        height: `${height}px`,
        width: `${width}px`,
      }}
      onClick={() => onSelect(book)}
    >
      {isTbr ? <span className="spine-tbr-flag">TBR</span> : null}
      <span className="spine-title">{book.title}</span>
      <span className="spine-author">{book.author}</span>
    </button>
  )
}

export default BookSpine

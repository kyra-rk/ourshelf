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

// Spine thickness follows page count, like a real book.
function widthFor(pageCount) {
  if (!pageCount) return 40
  return Math.min(70, Math.max(32, Math.round(pageCount / 12)))
}

function BookSpine({ book, onSelect }) {
  const color = spineColorFor(book.id)
  const textColor = textColorFor(color)
  const height = heightFor(book.id)
  const width = widthFor(book.pageCount)

  return (
    <button
      type="button"
      className="book-spine"
      style={{
        '--spine-color': color,
        color: textColor,
        height: `${height}px`,
        width: `${width}px`,
      }}
      onClick={() => onSelect(book)}
    >
      <span className="spine-title">{book.title}</span>
      <span className="spine-author">{book.author}</span>
    </button>
  )
}

export default BookSpine

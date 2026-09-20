import { Link } from 'react-router-dom'
import { SPINE_COLORS, textColorFor } from '../utils/palette.js'

function GenreFolder({ genre, count, index }) {
  const color = SPINE_COLORS[index % SPINE_COLORS.length]
  const textColor = textColorFor(color)
  const code = `FOLDER_${String(index + 1).padStart(2, '0')} //`

  return (
    <Link
      to={`/genre/${encodeURIComponent(genre)}`}
      className="folder-column"
      style={{ '--folder-color': color, color: textColor }}
    >
      <span className="folder-code">{code}</span>
      <span className="folder-title">{genre}</span>
      <span className="folder-count">
        {count} {count === 1 ? 'book' : 'books'}
      </span>
    </Link>
  )
}

export default GenreFolder

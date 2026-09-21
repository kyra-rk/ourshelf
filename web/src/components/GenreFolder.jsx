import { Link } from 'react-router-dom'
import { textColorFor } from '../utils/palette.js'
import { getGenreColor } from '../utils/genres.js'

// Tabs cascade left-to-right and overlap into the next folder, like the
// staggered index tabs in brainstorming/genre_folders.jpeg, instead of
// sitting flush at the top of each column.
const TAB_STAGGER_PX = 22

function GenreFolder({ genre, count, index, total }) {
  const color = getGenreColor(genre)
  const textColor = textColorFor(color)
  const zIndex = total - index

  return (
    <Link
      to={`/genre/${encodeURIComponent(genre)}`}
      className="folder-column"
      style={{ '--folder-color': color, color: textColor, zIndex }}
    >
      <span
        className="folder-tab"
        style={{ top: `${index * TAB_STAGGER_PX}px`, background: color, borderColor: 'rgba(0, 0, 0, 0.35)' }}
      />
      <span className="folder-title">{genre}</span>
      <span className="folder-count">
        {count} {count === 1 ? 'book' : 'books'}
      </span>
    </Link>
  )
}

export default GenreFolder

import GenreFolder from '../components/GenreFolder.jsx'
import { getGenreFolders } from '../utils/genres.js'

function GenresPage() {
  const folders = getGenreFolders()

  return (
    <main className="genres-page">
      <header className="page-header">
        <h1>ourshelf</h1>
        <p className="subtitle">pick a genre to browse the shelf</p>
      </header>
      <div className="folder-row">
        {folders.map(({ genre, count }, index) => (
          <GenreFolder key={genre} genre={genre} count={count} index={index} />
        ))}
      </div>
    </main>
  )
}

export default GenresPage

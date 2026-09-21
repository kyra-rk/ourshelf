import GenreFolder from '../components/GenreFolder.jsx'
import StatsScorecard from '../components/StatsScorecard.jsx'
import PeopleRow from '../components/PeopleRow.jsx'
import { getGenreFolders } from '../utils/genres.js'

function GenresPage() {
  const folders = getGenreFolders()

  return (
    <main className="genres-page">
      <header className="page-header">
        <h1>ourshelf</h1>
      </header>
      <div className="dashboard">
        <StatsScorecard />
        <PeopleRow />
      </div>
      <div className="folder-row">
        {folders.map(({ genre, count }, index) => (
          <GenreFolder key={genre} genre={genre} count={count} index={index} total={folders.length} />
        ))}
      </div>
    </main>
  )
}

export default GenresPage

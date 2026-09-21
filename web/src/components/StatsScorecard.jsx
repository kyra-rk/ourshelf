import { getStats } from '../utils/people.js'

function StatsScorecard() {
  const stats = getStats()

  const tiles = [
    { label: 'books read', value: stats.totalUniqueBooksRead },
    { label: 'combined shelf', value: stats.totalReadInstances },
    { label: 'overlap', value: `${stats.overlapPercent}%`, hint: `${stats.overlapBooks} shared` },
    { label: 'on the tbr pile', value: stats.totalUniqueBooksTbr },
  ]

  return (
    <section className="scorecard">
      <div className="scorecard-tiles">
        {tiles.map((tile) => (
          <div key={tile.label} className="scorecard-tile">
            <span className="scorecard-value">{tile.value}</span>
            <span className="scorecard-label">{tile.label}</span>
            {tile.hint ? <span className="scorecard-hint">{tile.hint}</span> : null}
          </div>
        ))}
      </div>
      {stats.topSharedBooks.length > 0 ? (
        <div className="scorecard-shared">
          <span className="scorecard-shared-label">you both read</span>
          <span className="scorecard-shared-list">
            {stats.topSharedBooks.map((book) => book.title).join(' · ')}
          </span>
        </div>
      ) : null}
    </section>
  )
}

export default StatsScorecard

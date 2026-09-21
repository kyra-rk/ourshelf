import readerCards from '../data/readerCards.json'

function initials(name) {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function ReaderIdCard({ person }) {
  const card = readerCards[person.id]
  if (!card) return null

  return (
    <div className="id-card">
      <div className="id-card-top">
        <div
          className="id-card-portrait"
          style={{ backgroundImage: person.avatarUrl ? `url(${person.avatarUrl})` : undefined }}
        >
          {person.avatarUrl ? null : initials(person.name)}
        </div>
        <div className="id-card-heading">
          <span className="id-card-title">READER PASS</span>
          <span className="id-card-name">{person.name}</span>
          <span className="id-card-code">CODE_{person.id.toUpperCase()} // OURSHELF</span>
        </div>
      </div>

      <dl className="id-card-fields">
        <div className="id-card-field">
          <dt>Fav genre</dt>
          <dd>{card.favGenre}</dd>
        </div>
        <div className="id-card-field">
          <dt>Medium</dt>
          <dd>{card.medium}</dd>
        </div>
        <div className="id-card-field">
          <dt>Skim rate</dt>
          <dd>{card.skimRate}</dd>
        </div>
        <div className="id-card-field">
          <dt>Reading speed</dt>
          <dd>{card.readingSpeed}</dd>
        </div>
      </dl>

      <div className="id-card-footer">
        <span className="id-card-stripe">* {person.readCount} BOOKS *</span>
        <span className="id-card-barcode" aria-hidden="true" />
      </div>
    </div>
  )
}

export default ReaderIdCard

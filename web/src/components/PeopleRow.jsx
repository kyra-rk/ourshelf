import { Link } from 'react-router-dom'
import { getPeople } from '../utils/people.js'

function initials(name) {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function PeopleRow() {
  const people = getPeople()

  return (
    <nav className="people-row" aria-label="Reader profiles">
      {people.map((person) => (
        <Link key={person.id} to={`/person/${person.id}`} className="people-card">
          <span className="people-avatar" style={{ backgroundImage: person.avatarUrl ? `url(${person.avatarUrl})` : undefined }}>
            {person.avatarUrl ? null : initials(person.name)}
          </span>
          <span className="people-name">{person.name}</span>
          <span className="people-count">{person.readCount} read</span>
        </Link>
      ))}
    </nav>
  )
}

export default PeopleRow

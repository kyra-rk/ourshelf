import { Link } from 'react-router-dom'
import PeopleRow from '../components/PeopleRow.jsx'

function PeoplePage() {
  return (
    <main className="shelf-page">
      <header className="shelf-header">
        <Link to="/" className="back-button">
          ← ourshelf
        </Link>
        <h1>reader profiles</h1>
      </header>
      <PeopleRow />
    </main>
  )
}

export default PeoplePage

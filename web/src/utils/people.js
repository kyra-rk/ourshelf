import people from '../data/people.json'
import stats from '../data/stats.json'

export function getPeople() {
  return people
}

export function getPersonById(id) {
  return people.find((person) => person.id === id)
}

export function getStats() {
  return stats
}

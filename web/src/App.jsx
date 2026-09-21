import { Route, Routes } from 'react-router-dom'
import NavMenu from './components/NavMenu.jsx'
import GenresPage from './pages/GenresPage.jsx'
import ShelfPage from './pages/ShelfPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import PeoplePage from './pages/PeoplePage.jsx'
import './App.css'

function App() {
  return (
    <>
      <NavMenu />
      <Routes>
        <Route path="/" element={<GenresPage />} />
        <Route path="/genre/:genre" element={<ShelfPage />} />
        <Route path="/person/:id" element={<ProfilePage />} />
        <Route path="/people" element={<PeoplePage />} />
      </Routes>
    </>
  )
}

export default App

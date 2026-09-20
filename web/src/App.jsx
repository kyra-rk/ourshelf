import { Route, Routes } from 'react-router-dom'
import GenresPage from './pages/GenresPage.jsx'
import ShelfPage from './pages/ShelfPage.jsx'
import './App.css'

function App() {
  return (
    <Routes>
      <Route path="/" element={<GenresPage />} />
      <Route path="/genre/:genre" element={<ShelfPage />} />
    </Routes>
  )
}

export default App

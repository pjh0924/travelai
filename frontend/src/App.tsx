import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ResultPage from './pages/ResultPage'
import SharePage from './pages/SharePage'
import PersonalityFormPage from './pages/PersonalityFormPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/personality" element={<PersonalityFormPage />} />
      <Route path="/result/:courseId" element={<ResultPage />} />
      <Route path="/share/:shareCode" element={<SharePage />} />
    </Routes>
  )
}

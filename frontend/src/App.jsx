import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout.jsx'
import BriefPage from './pages/BriefPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import ResearchPage from './pages/ResearchPage.jsx'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<ResearchPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/briefs/:sessionId" element={<BriefPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

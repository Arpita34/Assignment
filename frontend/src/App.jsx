// src/App.jsx — React Router with all 8 pages
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import SurveyConfig from './pages/SurveyConfig';
import GenerationDashboard from './pages/GenerationDashboard';
import ResponseExplorer from './pages/ResponseExplorer';
import Analytics from './pages/Analytics';
import PersonaInspector from './pages/PersonaInspector';
import CoherenceReview from './pages/CoherenceReview';
import RunHistory from './pages/RunHistory';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<SurveyConfig />} />
            <Route path="/generate" element={<GenerationDashboard />} />
            <Route path="/responses" element={<ResponseExplorer />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/personas" element={<PersonaInspector />} />
            <Route path="/review" element={<CoherenceReview />} />
            <Route path="/history" element={<RunHistory />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

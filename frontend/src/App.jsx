import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import ResearchWorkspace from './pages/ResearchWorkspace/ResearchWorkspace';
import PaperAnalysis from './pages/PaperAnalysis/PaperAnalysis';
import ComparePapers from './pages/ComparePapers/ComparePapers';
import ClaimVerification from './pages/ClaimVerification/ClaimVerification';
import Podcast from './pages/Podcast/Podcast';
import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/workspace" element={<ResearchWorkspace />} />
          <Route path="/analysis" element={<PaperAnalysis />} />
          <Route path="/compare" element={<ComparePapers />} />
          <Route path="/verify" element={<ClaimVerification />} />
          <Route path="/podcast" element={<Podcast />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;

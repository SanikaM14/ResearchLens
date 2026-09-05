import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import ResearchWorkspace from './pages/ResearchWorkspace/ResearchWorkspace';
import PaperAnalysis from './pages/PaperAnalysis/PaperAnalysis';
import ComparePapers from './pages/ComparePapers/ComparePapers';
import ClaimVerification from './pages/ClaimVerification/ClaimVerification';
import Podcast from './pages/Podcast/Podcast';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import './App.css';

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        <Route
          path="/*"
          element={
            <PrivateRoute>
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
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;

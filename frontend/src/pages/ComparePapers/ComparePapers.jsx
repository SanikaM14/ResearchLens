import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import EvidenceViewer from '../../components/EvidenceViewer/EvidenceViewer';
import LoadingSpinner from '../../components/LoadingSpinner/LoadingSpinner';
import styles from './ComparePapers.module.css';

export default function ComparePapers() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [flatEvidence, setFlatEvidence] = useState([]);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const data = await api.getDocuments();
      const readyDocs = data?.filter(doc => doc.status?.toLowerCase() === 'ready') || [];
      setDocuments(readyDocs);
    } catch (err) {
      console.error('Failed to fetch documents', err);
    }
  };

  const handleToggleDoc = (docId) => {
    setSelectedDocIds(prev => {
      if (prev.includes(docId)) {
        return prev.filter(id => id !== docId);
      } else {
        if (prev.length >= 5) {
          alert('You can compare a maximum of 5 papers at a time.');
          return prev;
        }
        return [...prev, docId];
      }
    });
  };

  const handleCompare = async () => {
    if (selectedDocIds.length < 2) {
      alert('Please select at least 2 papers to compare.');
      return;
    }
    if (!question.trim()) {
      alert('Please enter a comparison question.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setFlatEvidence([]);

    try {
      const data = await api.comparePapers(selectedDocIds, question);
      setResult(data);
      
      // Flatten the per-paper evidence dictionary into a single array for EvidenceViewer
      if (data.per_paper_evidence) {
        const flattened = Object.values(data.per_paper_evidence).flat();
        setFlatEvidence(flattened);
      }
    } catch (err) {
      setError(err.message || 'Failed to compare papers');
    } finally {
      setLoading(false);
    }
  };

  const renderHTMLTable = (htmlString) => {
    if (!htmlString) return null;
    return (
      <div 
        className={styles.tableWrapper}
        dangerouslySetInnerHTML={{ __html: htmlString }} 
      />
    );
  };

  return (
    <div className={styles.compare}>
      <header className={styles.header}>
        <div className={styles.titleSection}>
          <span className={styles.sectionNumber}>04</span>
          <h2>Compare Papers</h2>
        </div>
      </header>

      <div className={styles.setupSection}>
        <div className={styles.docSelector}>
          <h3>Select Papers (2-5)</h3>
          <div className={styles.chips}>
            {documents.length === 0 ? (
              <span className={styles.noDocs}>No ready documents available.</span>
            ) : (
              documents.map(doc => (
                <label 
                  key={doc.id} 
                  className={`${styles.chip} ${selectedDocIds.includes(doc.id) ? styles.chipSelected : ''}`}
                >
                  <input 
                    type="checkbox" 
                    checked={selectedDocIds.includes(doc.id)}
                    onChange={() => handleToggleDoc(doc.id)}
                    className={styles.hiddenCheckbox}
                  />
                  {doc.original_name}
                </label>
              ))
            )}
          </div>
        </div>

        <div className={styles.inputArea}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What would you like to compare? (e.g., 'Compare the methodologies used in these papers')"
            className={styles.input}
            disabled={loading}
          />
          <button 
            className={`btn-primary ${styles.compareBtn}`}
            onClick={handleCompare}
            disabled={loading || selectedDocIds.length < 2 || !question.trim()}
          >
            {loading ? 'Comparing...' : 'Compare'}
          </button>
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {loading && (
        <div className={styles.loadingContainer}>
          <LoadingSpinner message="Analyzing and comparing selected papers..." />
        </div>
      )}

      {!loading && !result && !error && (
        <div className={styles.emptyState}>
          <p>Select at least two papers and ask a question to generate a comparison.</p>
        </div>
      )}

      {result && (
        <div className={styles.resultsArea}>
          <div className={styles.answerCard}>
            <h3>Comparison Summary</h3>
            <div 
              className={styles.answerText}
              dangerouslySetInnerHTML={{ 
                __html: result.answer.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
              }}
            />
          </div>

          {result.comparison_table && (
            <div className={styles.tableCard}>
              <h3>Detailed Comparison</h3>
              {renderHTMLTable(result.comparison_table)}
            </div>
          )}

          <div className={styles.evidenceSection}>
            <h3>Evidence Used</h3>
            <EvidenceViewer evidenceList={flatEvidence} />
          </div>
        </div>
      )}
    </div>
  );
}

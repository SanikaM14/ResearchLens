import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import VerdictBadge from '../../components/VerdictBadge/VerdictBadge';
import CitationCard from '../../components/CitationCard/CitationCard';
import LoadingSpinner from '../../components/LoadingSpinner/LoadingSpinner';
import styles from './ClaimVerification.module.css';

export default function ClaimVerification() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [claim, setClaim] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const data = await api.getDocuments();
      const readyDocs = data?.filter(doc => doc.status?.toLowerCase() === 'ready') || [];
      setDocuments(readyDocs);
      if (readyDocs.length > 0) {
        setSelectedDocId(readyDocs[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch documents', err);
    }
  };

  const handleVerify = async () => {
    if (!selectedDocId || !claim.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.verifyClaim(selectedDocId, claim);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to verify claim');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.verification}>
      <header className={styles.header}>
        <div className={styles.titleSection}>
          <span className={styles.sectionNumber}>05</span>
          <h2>Claim Verification</h2>
        </div>
      </header>

      <div className={styles.setupSection}>
        <select 
          value={selectedDocId} 
          onChange={(e) => setSelectedDocId(e.target.value)}
          className={styles.select}
          disabled={loading || documents.length === 0}
        >
          <option value="" disabled>Select a document to check against</option>
          {documents.map(doc => (
            <option key={doc.id} value={doc.id}>
              {doc.original_name}
            </option>
          ))}
        </select>

        <textarea
          value={claim}
          onChange={(e) => setClaim(e.target.value)}
          placeholder="Enter a claim to verify... (e.g., 'The study found a 50% increase in performance')"
          className={styles.textarea}
          disabled={loading}
          rows={3}
        />

        <button 
          className={`btn-primary ${styles.verifyBtn}`}
          onClick={handleVerify}
          disabled={loading || !selectedDocId || !claim.trim()}
        >
          {loading ? 'Verifying...' : 'Verify Claim'}
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {loading && (
        <div className={styles.loadingContainer}>
          <LoadingSpinner message="Cross-referencing claim with document evidence..." />
        </div>
      )}

      {!loading && !result && !error && (
        <div className={styles.emptyState}>
          <p>Select a paper, enter a claim, and click Verify to fact-check it.</p>
        </div>
      )}

      {result && (
        <div className={styles.resultsArea}>
          <div className={styles.verdictSection}>
            <VerdictBadge verdict={result.verdict} />
            <div className={styles.explanation}>
              <p>{result.explanation}</p>
            </div>
          </div>

          <div className={styles.evidenceColumns}>
            <div className={styles.evidenceColumn}>
              <h3 className={styles.supportingTitle}>Supporting Evidence</h3>
              {result.supporting_evidence && result.supporting_evidence.length > 0 ? (
                <div className={styles.evidenceList}>
                  {result.supporting_evidence.map((ev, idx) => (
                    <CitationCard key={idx} evidence={ev} />
                  ))}
                </div>
              ) : (
                <p className={styles.noEvidence}>No supporting evidence found.</p>
              )}
            </div>

            <div className={styles.evidenceColumn}>
              <h3 className={styles.contradictingTitle}>Contradicting Evidence</h3>
              {result.contradicting_evidence && result.contradicting_evidence.length > 0 ? (
                <div className={styles.evidenceList}>
                  {result.contradicting_evidence.map((ev, idx) => (
                    <CitationCard key={idx} evidence={ev} />
                  ))}
                </div>
              ) : (
                <p className={styles.noEvidence}>No contradicting evidence found.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

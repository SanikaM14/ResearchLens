import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import CitationCard from '../../components/CitationCard/CitationCard';
import LoadingSpinner from '../../components/LoadingSpinner/LoadingSpinner';
import styles from './PaperAnalysis.module.css';

export default function PaperAnalysis() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
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

  const handleAnalyze = async () => {
    if (!selectedDocId) return;
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const data = await api.analyzeDocument(selectedDocId);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to analyze paper');
    } finally {
      setLoading(false);
    }
  };

  const renderSection = (section) => {
    if (!section) return null;
    
    return (
      <div className={styles.sectionCard} key={section.title}>
        <div className={styles.sectionHeader}>
          <div className={styles.accentBlock}></div>
          <h3>{section.title}</h3>
        </div>
        
        {section.content && (
          <div className={styles.sectionContent}>
            {section.content.split('\n').filter(p => p.trim()).map((para, i) => (
              <p key={i}>{para}</p>
            ))}
          </div>
        )}
        
        {section.citations && section.citations.length > 0 && (
          <div className={styles.evidenceArea}>
            <h4 className={styles.evidenceTitle}>
              Supporting Evidence ({section.citations.length})
            </h4>
            <div className={styles.evidenceList}>
              {section.citations.map((ev, idx) => (
                <CitationCard key={idx} evidence={ev} />
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={styles.analysis}>
      <header className={styles.header}>
        <div className={styles.titleSection}>
          <span className={styles.sectionNumber}>03</span>
          <h2>Paper Analysis</h2>
        </div>
      </header>

      <div className={styles.controls}>
        <select 
          value={selectedDocId} 
          onChange={(e) => setSelectedDocId(e.target.value)}
          className={styles.select}
          disabled={loading || documents.length === 0}
        >
          <option value="" disabled>Select a document to analyze</option>
          {documents.map(doc => (
            <option key={doc.id} value={doc.id}>
              {doc.original_name}
            </option>
          ))}
        </select>
        
        <button 
          className={`btn-primary ${styles.analyzeBtn}`} 
          onClick={handleAnalyze}
          disabled={!selectedDocId || loading}
        >
          {loading ? 'Analyzing...' : 'Analyze Paper'}
        </button>
        
        {result && (
          <button 
            className={`btn-secondary ${styles.printBtn}`}
            onClick={() => window.print()}
          >
            Export to PDF
          </button>
        )}
      </div>

      {error && <div className={styles.error}>{error}</div>}
      
      {loading && (
        <div className={styles.loadingContainer}>
          <LoadingSpinner message="Analyzing paper across 8 research dimensions..." />
        </div>
      )}

      {!loading && !result && !error && (
        <div className={styles.emptyState}>
          <p>Select a paper and click Analyze to generate a structured breakdown covering research problem, methodology, findings, metrics, limitations, and future work.</p>
        </div>
      )}

      {result && (
        <div className={styles.results}>
          <div className={styles.resultHeader}>
            <h3>{result.document_name}</h3>
            <span className={styles.processingTime}>
              Analyzed in {(result.processing_time_ms / 1000).toFixed(1)}s
            </span>
          </div>

          {/* Render all analysis sections from backend */}
          <div className={styles.grid}>
            {result.sections && result.sections.map((section) => renderSection(section))}
          </div>

          {/* Key Metrics Table */}
          {result.key_metrics && result.key_metrics.length > 0 && (
            <div className={styles.metricsCard}>
              <div className={styles.sectionHeader}>
                <div className={styles.accentBlock}></div>
                <h3>Key Metrics & Numbers</h3>
              </div>
              <div className={styles.metricsGrid}>
                {result.key_metrics.map((metric, idx) => (
                  <div key={idx} className={styles.metricItem}>
                    <div className={styles.metricValue}>{metric.value}</div>
                    <div className={styles.metricName}>{metric.metric}</div>
                    {metric.context && (
                      <div className={styles.metricContext}>{metric.context}</div>
                    )}
                    {metric.page && (
                      <div className={styles.metricSource}>Page {metric.page}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

import { useState } from 'react';
import styles from './CitationCard.module.css';

export default function CitationCard({ evidence }) {
  const [expanded, setExpanded] = useState(false);

  // ChromaDB distance: lower is better. Convert to a pseudo-percentage for UI if needed, or just show the score.
  // We'll show a simple bar assuming max distance ~2.0
  const scorePercent = evidence.relevance_score ? Math.max(0, 100 - (evidence.relevance_score * 50)) : null;

  return (
    <div className={styles.card}>
      <div className={styles.summary} onClick={() => setExpanded(!expanded)}>
        <div className={styles.indicator}></div>
        <div className={styles.tag}>
          [{evidence.document_name ? `${evidence.document_name}, ` : ''}Page {evidence.page_number || '?'}{evidence.section ? `, ${evidence.section}` : ''}]
        </div>
        {scorePercent !== null && (
          <div className={styles.scoreBar} title={`Distance Score: ${evidence.relevance_score}`}>
            <div 
              className={styles.scoreFill} 
              style={{ width: `${Math.min(100, Math.max(5, scorePercent))}%` }}
            ></div>
          </div>
        )}
        <button className={styles.toggleBtn}>
          {expanded ? '−' : '+'}
        </button>
      </div>
      
      {expanded && (
        <div className={styles.content}>
          <pre className={styles.text}>{evidence.evidence_text}</pre>
        </div>
      )}
    </div>
  );
}

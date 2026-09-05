import CitationCard from '../CitationCard/CitationCard';
import styles from './EvidenceViewer.module.css';

export default function EvidenceViewer({ evidenceList = [] }) {
  if (!evidenceList || evidenceList.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h4>Sources & Evidence</h4>
          <span className={styles.badge}>0</span>
        </div>
        <div className={styles.empty}>
          <p>No evidence found for this query.</p>
        </div>
      </div>
    );
  }

  // Group by document
  const groupedEvidence = evidenceList.reduce((acc, ev) => {
    const docName = ev.document_name || 'Unknown Document';
    if (!acc[docName]) {
      acc[docName] = [];
    }
    acc[docName].push(ev);
    return acc;
  }, {});

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h4>Sources & Evidence</h4>
        <span className={styles.badge}>{evidenceList.length}</span>
      </div>
      
      <div className={styles.content}>
        {Object.entries(groupedEvidence).map(([docName, items], index) => (
          <div key={index} className={styles.documentGroup}>
            <h5 className={styles.documentTitle}>{docName}</h5>
            <div className={styles.evidenceList}>
              {items.map((ev, i) => (
                <CitationCard key={i} evidence={ev} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

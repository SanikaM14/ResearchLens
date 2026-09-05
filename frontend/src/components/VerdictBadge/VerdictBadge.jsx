import styles from './VerdictBadge.module.css';

export default function VerdictBadge({ verdict }) {
  if (!verdict) return null;

  const normalizedVerdict = verdict.toUpperCase().replace(/\s+/g, '_');
  
  let badgeClass = '';
  let icon = '';
  let label = verdict;

  if (normalizedVerdict.includes('SUPPORTED') && !normalizedVerdict.includes('PARTIALLY') && !normalizedVerdict.includes('NOT')) {
    badgeClass = styles.supported;
    icon = <i className="bi bi-check-circle-fill"></i>;
    label = 'Supported';
  } else if (normalizedVerdict.includes('PARTIALLY')) {
    badgeClass = styles.partially;
    icon = <i className="bi bi-exclamation-triangle-fill"></i>;
    label = 'Partially Supported';
  } else if (normalizedVerdict.includes('NOT') || normalizedVerdict.includes('CONTRADICTED')) {
    badgeClass = styles.notSupported;
    icon = <i className="bi bi-x-circle-fill"></i>;
    label = 'Not Supported';
  } else {
    badgeClass = styles.unknown;
    icon = <i className="bi bi-question-circle-fill"></i>;
  }

  return (
    <div className={`${styles.badge} ${badgeClass}`}>
      <span className={styles.icon}>{icon}</span>
      <span className={styles.label}>{label}</span>
    </div>
  );
}

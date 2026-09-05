import styles from './DocumentCard.module.css';

export default function DocumentCard({ document, onDelete, onSelect, selected }) {
  const handleDelete = (e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this document?')) {
      onDelete(document.id);
    }
  };

  const getStatusBadge = (status) => {
    switch(status?.toLowerCase()) {
      case 'ready':
        return <span className={`${styles.badge} ${styles.ready}`}>Ready</span>;
      case 'processing':
        return <span className={`${styles.badge} ${styles.processing}`}>Processing</span>;
      case 'failed':
        return <span className={`${styles.badge} ${styles.failed}`}>Failed</span>;
      default:
        return <span className={styles.badge}>{status}</span>;
    }
  };

  return (
    <div 
      className={`${styles.card} ${selected ? styles.selected : ''} ${onSelect ? styles.selectable : ''}`}
      onClick={() => onSelect && onSelect(document)}
    >
      <div className={styles.header}>
        <h3 className={styles.title} title={document.original_name}>
          {document.original_name}
        </h3>
        {getStatusBadge(document.status)}
      </div>
      
      <div className={styles.meta}>
        {document.total_pages && <span>{document.total_pages} pages</span>}
        {document.file_size && <span>{(document.file_size / (1024 * 1024)).toFixed(2)} MB</span>}
        {document.upload_time && <span>{new Date(document.upload_time).toLocaleDateString()}</span>}
      </div>
      
      {onDelete && (
        <button className={styles.deleteBtn} onClick={handleDelete} title="Delete document">
          <i className="bi bi-trash"></i>
        </button>
      )}
    </div>
  );
}

import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import FileUpload from '../../components/FileUpload/FileUpload';
import DocumentCard from '../../components/DocumentCard/DocumentCard';
import LoadingSpinner from '../../components/LoadingSpinner/LoadingSpinner';
import styles from './Dashboard.module.css';

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const data = await api.getDocuments();
      setDocuments(data || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch documents', err);
      setError('Failed to load documents. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUpload = async (file) => {
    try {
      setLoading(true);
      await api.uploadDocument(file);
      await fetchDocuments();
    } catch (err) {
      console.error('Upload failed', err);
      alert('Upload failed: ' + err.message);
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteDocument(id);
      setDocuments(documents.filter(doc => doc.id !== id));
    } catch (err) {
      console.error('Delete failed', err);
      alert('Delete failed: ' + err.message);
    }
  };

  const totalDocs = documents.length;
  const totalPages = documents.reduce((sum, doc) => sum + (doc.total_pages || 0), 0);

  return (
    <div className={styles.dashboard}>
      <header className={styles.header}>
        <div className={styles.titleSection}>
          <span className={styles.sectionNumber}>01</span>
          <h2>Dashboard</h2>
        </div>
      </header>

      <section className={styles.uploadSection}>
        <FileUpload onUpload={handleUpload} />
      </section>

      <section className={styles.statsBar}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Total Documents</span>
          <span className={styles.statValue}>{totalDocs}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Total Pages Processed</span>
          <span className={styles.statValue}>{totalPages}</span>
        </div>
      </section>

      <section className={styles.librarySection}>
        <div className={styles.libraryHeader}>
          <h3>Document Library</h3>
          <button className={styles.refreshBtn} onClick={fetchDocuments} title="Refresh">
            <i className="bi bi-arrow-clockwise"></i>
          </button>
        </div>
        
        {loading && !documents.length ? (
          <LoadingSpinner message="Loading documents..." />
        ) : error ? (
          <div className={styles.error}>{error}</div>
        ) : documents.length === 0 ? (
          <div className={styles.emptyState}>
            <p>Upload your first research paper to get started.</p>
          </div>
        ) : (
          <div className={styles.grid}>
            {documents.map(doc => (
              <DocumentCard 
                key={doc.id} 
                document={doc} 
                onDelete={handleDelete} 
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

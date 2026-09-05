import { useState, useRef } from 'react';
import styles from './FileUpload.module.css';

export default function FileUpload({ onUpload }) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (selectedFile) => {
    if (selectedFile.type !== 'application/pdf') {
      alert('Please upload a PDF file.');
      return;
    }
    setFile(selectedFile);
  };

  const handleUpload = () => {
    if (file && onUpload) {
      onUpload(file);
      setFile(null); // Reset after upload triggered
    }
  };

  return (
    <div className={styles.container}>
      <div 
        className={`${styles.dropZone} ${isDragging ? styles.dragging : ''} ${file ? styles.hasFile : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !file && fileInputRef.current.click()}
      >
        <input 
          type="file" 
          accept="application/pdf"
          ref={fileInputRef}
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        
        {file ? (
          <div className={styles.fileInfo}>
            <span className={styles.icon}><i className="bi bi-file-earmark-pdf"></i></span>
            <div className={styles.details}>
              <p className={styles.fileName}>{file.name}</p>
              <p className={styles.fileSize}>{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
            </div>
            <button className={styles.removeBtn} onClick={(e) => { e.stopPropagation(); setFile(null); }}><i className="bi bi-x-lg"></i></button>
          </div>
        ) : (
          <div className={styles.prompt}>
            <span className={styles.uploadIcon}><i className="bi bi-cloud-arrow-up"></i></span>
            <p>Drop your research paper here</p>
            <span>or click to browse (.pdf)</span>
          </div>
        )}
      </div>
      
      {file && (
        <button className={`btn-primary ${styles.uploadBtn}`} onClick={handleUpload}>
          Upload Document
        </button>
      )}
    </div>
  );
}

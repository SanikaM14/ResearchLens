import { useState, useEffect, useRef } from 'react';
import { api } from '../../services/api';
import LoadingSpinner from '../../components/LoadingSpinner/LoadingSpinner';
import styles from './Podcast.module.css';

export default function Podcast() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [loading, setLoading] = useState(false);
  const [script, setScript] = useState(null);
  const [error, setError] = useState(null);
  
  // Audio playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentLineIndex, setCurrentLineIndex] = useState(-1);
  const synth = window.speechSynthesis;
  const utteranceRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
    return () => {
      // Cleanup audio on unmount
      if (synth.speaking) synth.cancel();
    };
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

  const handleGenerate = async () => {
    if (!selectedDocId) return;
    setLoading(true);
    setError(null);
    setScript(null);
    if (synth.speaking) synth.cancel();
    setIsPlaying(false);
    setCurrentLineIndex(-1);

    try {
      const data = await api.generatePodcast(selectedDocId);
      setScript(data.script);
    } catch (err) {
      setError(err.message || 'Failed to generate podcast script');
    } finally {
      setLoading(false);
    }
  };

  const playLine = (index) => {
    if (!script || index >= script.length) {
      setIsPlaying(false);
      setCurrentLineIndex(-1);
      return;
    }

    setCurrentLineIndex(index);
    const line = script[index];
    const utterance = new SpeechSynthesisUtterance(line.text);
    
    // Different voices for different hosts if possible
    const voices = synth.getVoices();
    if (voices.length > 0) {
      if (line.speaker.includes("2")) {
        // Try to pick a female/alternate voice for Host 2
        utterance.voice = voices.find(v => v.name.includes('Female') || v.name.includes('Zira')) || voices[1] || voices[0];
        utterance.pitch = 1.2;
      } else {
        utterance.voice = voices.find(v => v.name.includes('Male') || v.name.includes('David')) || voices[0];
        utterance.pitch = 1.0;
      }
    }

    utterance.rate = 1.1; // Slightly faster for podcast feel
    
    utterance.onend = () => {
      playLine(index + 1);
    };
    
    utterance.onerror = (e) => {
      console.error("Speech error", e);
      setIsPlaying(false);
    };

    utteranceRef.current = utterance;
    synth.speak(utterance);
  };

  const togglePlayback = () => {
    if (isPlaying) {
      synth.cancel();
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      playLine(currentLineIndex === -1 ? 0 : currentLineIndex);
    }
  };

  return (
    <div className={styles.podcast}>
      <header className={styles.header}>
        <div className={styles.titleSection}>
          <span className={styles.sectionNumber}>06</span>
          <h2>Paper-to-Podcast</h2>
        </div>
      </header>

      <div className={styles.controls}>
        <select 
          value={selectedDocId} 
          onChange={(e) => setSelectedDocId(e.target.value)}
          className={styles.select}
          disabled={loading || documents.length === 0}
        >
          <option value="" disabled>Select a paper to summarize</option>
          {documents.map(doc => (
            <option key={doc.id} value={doc.id}>
              {doc.original_name}
            </option>
          ))}
        </select>
        
        <button 
          className={`btn-primary ${styles.generateBtn}`} 
          onClick={handleGenerate}
          disabled={!selectedDocId || loading}
        >
          {loading ? 'Generating Script...' : 'Generate Audio Brief'}
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}
      
      {loading && (
        <div className={styles.loadingContainer}>
          <LoadingSpinner message="AI is reading the paper and writing a podcast script..." />
        </div>
      )}

      {script && script.length > 0 && !loading && (
        <div className={styles.playerContainer}>
          <div className={styles.audioControls}>
            <button className={styles.playBtn} onClick={togglePlayback}>
              {isPlaying ? '⏹ Stop Audio' : '▶ Play Podcast'}
            </button>
            <p className={styles.helperText}>Uses your browser's built-in text-to-speech engine.</p>
          </div>
          
          <div className={styles.scriptArea}>
            {script.map((line, idx) => (
              <div 
                key={idx} 
                className={`${styles.dialogueLine} ${line.speaker.includes('2') ? styles.host2 : styles.host1} ${idx === currentLineIndex ? styles.activeLine : ''}`}
                onClick={() => {
                  if (synth.speaking) synth.cancel();
                  setIsPlaying(true);
                  playLine(idx);
                }}
              >
                <div className={styles.speaker}>{line.speaker}</div>
                <div className={styles.text}>{line.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {script && script.length === 0 && !loading && (
        <div className={styles.emptyState}>
          <p>Failed to generate podcast script. The AI API key may be rate limited.</p>
        </div>
      )}
    </div>
  );
}

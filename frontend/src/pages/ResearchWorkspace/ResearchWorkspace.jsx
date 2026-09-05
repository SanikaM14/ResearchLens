import { useState, useEffect, useRef } from 'react';
import { api } from '../../services/api';
import EvidenceViewer from '../../components/EvidenceViewer/EvidenceViewer';
import LoadingSpinner from '../../components/LoadingSpinner/LoadingSpinner';
import styles from './ResearchWorkspace.module.css';

export default function ResearchWorkspace() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [useAgent, setUseAgent] = useState(false);
  const [currentEvidence, setCurrentEvidence] = useState([]);
  const chatEndRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const fetchDocuments = async () => {
    try {
      const data = await api.getDocuments();
      // Only allow selecting ready documents
      const readyDocs = data?.filter(doc => doc.status?.toLowerCase() === 'ready') || [];
      setDocuments(readyDocs);
    } catch (err) {
      console.error('Failed to fetch documents', err);
    }
  };

  const handleToggleDoc = (docId) => {
    setSelectedDocIds(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || selectedDocIds.length === 0) return;

    const newQuery = query;
    setQuery('');
    setChatHistory(prev => [...prev, { role: 'user', content: newQuery }]);
    setLoading(true);

    try {
      const result = await api.queryResearch(newQuery, selectedDocIds, useAgent);
      
      setChatHistory(prev => [...prev, { 
        role: 'assistant', 
        content: result.answer,
        citations: result.citations
      }]);
      
      if (result.citations) {
        setCurrentEvidence(result.citations);
      }
    } catch (err) {
      setChatHistory(prev => [...prev, { 
        role: 'system', 
        content: `Error: ${err.message}` 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessageContent = (content) => {
    // Simple markdown-like rendering for bold and citations
    let html = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\[(\d+)\]/g, '<span class="citation-marker">[$1]</span>');
      
    // Handle newlines
    const paragraphs = html.split('\n').filter(p => p.trim());
    return paragraphs.map((p, i) => <p key={i} dangerouslySetInnerHTML={{ __html: p }} />);
  };

  return (
    <div className={styles.workspace}>
      <header className={styles.header}>
        <div className={styles.titleSection}>
          <span className={styles.sectionNumber}>02</span>
          <h2>Research Workspace</h2>
        </div>
      </header>

      <div className={styles.container}>
        <div className={styles.mainArea}>
          <div className={styles.docSelector}>
            <h3>Select Documents</h3>
            <div className={styles.chips}>
              {documents.length === 0 ? (
                <span className={styles.noDocs}>No ready documents available. Go to dashboard to upload.</span>
              ) : (
                documents.map(doc => (
                  <button
                    key={doc.id}
                    className={`${styles.chip} ${selectedDocIds.includes(doc.id) ? styles.chipSelected : ''}`}
                    onClick={() => handleToggleDoc(doc.id)}
                  >
                    {doc.original_name}
                  </button>
                ))
              )}
            </div>
            <div className={styles.agentToggle}>
              <label>
                <input 
                  type="checkbox" 
                  checked={useAgent} 
                  onChange={(e) => setUseAgent(e.target.checked)} 
                />
                Use Deep Agent Workflow (Slower, more thorough)
              </label>
            </div>
          </div>

          <div className={styles.chatArea}>
            {chatHistory.length === 0 ? (
              <div className={styles.emptyChat}>
                <span className={styles.emptyIcon}><i className="bi bi-chat-quote"></i></span>
                <p>Select documents above and ask a question to start researching.</p>
              </div>
            ) : (
              <div className={styles.messages}>
                {chatHistory.map((msg, idx) => (
                  <div key={idx} className={`${styles.message} ${styles[msg.role]}`}>
                    <div className={styles.messageContent}>
                      {msg.role === 'assistant' 
                        ? renderMessageContent(msg.content)
                        : <p>{msg.content}</p>
                      }
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className={styles.loadingMessage}>
                    <LoadingSpinner message={useAgent ? "Agent is researching..." : "Generating answer..."} />
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
            )}

            <form className={styles.inputArea} onSubmit={handleSubmit}>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question about the selected documents..."
                disabled={selectedDocIds.length === 0 || loading}
                className={styles.input}
              />
              <button 
                type="submit" 
                className={`btn-primary ${styles.sendBtn}`}
                disabled={!query.trim() || selectedDocIds.length === 0 || loading}
              >
                Send
              </button>
            </form>
          </div>
        </div>

        <div className={styles.sideArea}>
          <EvidenceViewer evidenceList={currentEvidence} />
        </div>
      </div>
    </div>
  );
}

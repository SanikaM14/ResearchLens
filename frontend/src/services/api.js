/**
 * ResearchLens API Service
 * All API calls to the FastAPI backend.
 * Handles errors gracefully and returns parsed JSON.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchWithHandler(url, options = {}) {
  const token = localStorage.getItem('token');
  const headers = options.headers ? new Headers(options.headers) : new Headers();
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  const updatedOptions = { ...options, headers };

  try {
    const response = await fetch(url, updatedOptions);
    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
        throw new Error('Session expired. Please log in again.');
      }
      let errorMsg = `Error ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        errorMsg = errorData.detail || errorMsg;
      } catch (e) {
        // Response wasn't JSON
      }
      throw new Error(errorMsg);
    }
    return await response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      throw new Error('Cannot connect to the server. Please make sure the backend is running.');
    }
    throw error;
  }
}

export const api = {
  // ─────────────────────────────────────
  // Documents
  // ─────────────────────────────────────

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    return fetchWithHandler(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
  },

  async getDocuments() {
    const data = await fetchWithHandler(`${API_BASE}/documents`);
    // Normalize response: backend returns { documents: [...], total: N }
    return data.documents || [];
  },

  async getDocument(id) {
    return fetchWithHandler(`${API_BASE}/documents/${id}`);
  },

  async deleteDocument(id) {
    return fetchWithHandler(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
    });
  },

  // ─────────────────────────────────────
  // Research (snake_case matches backend Pydantic models)
  // ─────────────────────────────────────

  async queryResearch(query, documentIds, useAgent = false) {
    return fetchWithHandler(`${API_BASE}/research/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        document_ids: documentIds,
        use_agent: useAgent,
      }),
    });
  },

  async analyzeDocument(documentId) {
    return fetchWithHandler(`${API_BASE}/research/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: documentId,
      }),
    });
  },

  async comparePapers(documentIds, question) {
    return fetchWithHandler(`${API_BASE}/research/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_ids: documentIds,
        question,
      }),
    });
  },

  async verifyClaim(documentId, claim) {
    return fetchWithHandler(`${API_BASE}/research/verify-claim`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: documentId,
        claim,
      }),
    });
  },

  async generatePodcast(documentId) {
    return fetchWithHandler(`${API_BASE}/research/podcast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: documentId,
      }),
    });
  },

  // ─────────────────────────────────────
  // Health
  // ─────────────────────────────────────

  async getHealth() {
    return fetchWithHandler(`${API_BASE}/health`);
  },
};

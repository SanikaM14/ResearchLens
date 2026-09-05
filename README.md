# ResearchLens

**Evidence-Grounded AI Research Paper Intelligence Platform**

> *"Do not just answer. Show where the answer came from."*

ResearchLens is a full-stack AI application that ingests research papers, performs semantic retrieval, answers questions with grounded evidence, extracts key findings and metrics, compares multiple papers, and provides verifiable citations — every answer traces back to the exact document, page, section, and evidence text.

---

## The Problem

Research papers are 20–50+ pages of dense, technical content. Users need:
- Specific answers to questions about methodology, findings, limitations
- Key numbers and metrics (accuracy, sample size, improvements)
- Cross-paper comparisons
- Claim verification against actual evidence

Existing "Chat with PDF" tools often **hallucinate**, give **vague summaries**, and **cannot prove where an answer came from**. ResearchLens solves this with a metadata-preserving RAG pipeline where every citation comes from stored metadata, never from LLM invention.

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                  React + Vite Frontend                     │
│  Dashboard │ Research Workspace │ Analysis │ Compare │      │
│                   Claim Verification                       │
└──────────────────────┬─────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼─────────────────────────────────────┐
│                   FastAPI Backend                           │
│                                                            │
│  PDF Extraction ──► Semantic Chunking ──► Embeddings       │
│  (PyMuPDF)         (page-aware)         (MiniLM-L6-v2)    │
│                                              │             │
│                                              ▼             │
│  Groq LLM ◄──── Retrieval Service ◄──── ChromaDB           │
│  (evidence-grounded)  │                (vectors+metadata)  │
│                       ▼                                    │
│              Citation Service                              │
│         (metadata-based, never invented)                   │
│                                                            │
│  LangGraph Workflow (complex multi-step queries)           │
│  SQLite (document metadata, ingestion state)               │
└────────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline

### 1. PDF Ingestion
- **PyMuPDF** extracts text **page by page** with reading order preservation
- Font size analysis detects **section headings** (Abstract, Methods, Results, etc.)
- Each page tagged with page number and detected sections

### 2. Semantic Chunking
- Text split at **paragraph and section boundaries** (not arbitrary character blocks)
- Each chunk carries metadata:
  ```json
  {
    "document_id": "uuid",
    "document_name": "paper.pdf",
    "page_number": 8,
    "section": "Results",
    "chunk_index": 24,
    "paragraph_index": 3,
    "text": "The proposed model achieved an accuracy of 94.2%..."
  }
  ```
- Configurable chunk size (default 512 tokens) with overlap (default 50 tokens)

### 3. Embedding & Vector Storage
- **Sentence-Transformers** (`all-MiniLM-L6-v2`) generates 384-dimensional embeddings locally
- **ChromaDB** stores vectors alongside full citation metadata
- Supports filtering by `document_id` for single-paper and multi-paper queries

### 4. Evidence-Grounded Retrieval
- User's question is embedded and matched against stored chunks
- Top-K most relevant chunks retrieved with metadata
- Evidence passed to Groq LLM with strict system prompt:
  - Answer ONLY from provided evidence
  - Never invent citations or page numbers
  - Clearly state when evidence is insufficient

### 5. Citation Generation
- **Citations come from ChromaDB metadata, NOT from LLM output**
- Each citation includes: document name, page number, section, evidence text, relevance score
- This is the critical difference from generic chatbots

---

## Why Metadata Preservation Matters

Without metadata:
> "The model achieved 94.2% accuracy." ← *Which page? Which paper? Is this real?*

With ResearchLens:
> "The model achieved 94.2% accuracy."
> **Source:** Example Paper, Page 8, Section: Results
> **Evidence:** *"The proposed model achieved an accuracy of 94.2% on the validation set, outperforming the baseline by 12%."*

This traceability is what makes the difference between a **toy demo** and a **useful research tool**.

---

## Multi-Paper Workflow

When comparing multiple papers:
1. Evidence is retrieved **separately per document** — sources never mixed
2. The LLM receives clearly labeled evidence: `[Paper A, Page 5]` vs `[Paper B, Page 12]`
3. Comparison tables preserve which claim came from which paper
4. Citations are grouped by document in the response

---

## Agentic Workflow (LangGraph)

For complex multi-step queries, ResearchLens uses a **LangGraph StateGraph**:

```
START → ANALYZE_QUERY → [single/multi routing]
                              │
              ┌───────────────┼───────────────┐
              ▼                               ▼
        RETRIEVE_SINGLE               RETRIEVE_MULTI
              │                               │
              └───────────┬───────────────────┘
                          ▼
                   CHECK_EVIDENCE
                     │         │
                  ENOUGH    NOT_ENOUGH → RETRIEVE_MORE (max 2 retries)
                     │                        │
                     └────────────────────────┘
                                │
                          SYNTHESIZE → ATTACH_SOURCES → END
```

This is only used for genuinely complex queries — simple Q&A uses the direct pipeline.

---

## Features

| Feature | Description |
|---------|-------------|
| **PDF Upload & Ingestion** | Upload PDFs with validation, extract text page-by-page |
| **Evidence-Grounded Q&A** | Ask questions, get answers with citations |
| **Structured Analysis** | Auto-extract: problem, methodology, findings, metrics, limitations |
| **Key Metrics Extraction** | Find important numbers (accuracy, dataset size, improvements) |
| **Multi-Paper Comparison** | Compare 2-5 papers with per-paper evidence |
| **Claim Verification** | Check if a claim is SUPPORTED, PARTIALLY_SUPPORTED, or NOT_CLEARLY_SUPPORTED |
| **LangGraph Workflows** | Complex multi-step research queries |

---

## Security

| Concern | Implementation |
|---------|---------------|
| **File Upload** | Extension + magic bytes + size validation, UUID filenames, no path traversal |
| **Prompt Injection** | Research text wrapped as DATA in `<RESEARCH_DATA>` tags, system prompt hardened |
| **API Security** | Pydantic validation, rate limiting (30 req/min/IP), no stack traces exposed |
| **Secrets** | API keys in env vars only, `.env` in `.gitignore`, never returned via API |
| **CORS** | Configurable allowed origins |
| **Data Deletion** | Full cleanup: disk + ChromaDB + SQLite |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 + Vite | SPA with editorial design |
| Backend | Python 3.11 + FastAPI | REST API |
| LLM | Groq API (llama-3.3-70b-versatile) | Evidence-grounded answers |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Local 384-dim embeddings |
| Vector DB | ChromaDB | Semantic search + metadata |
| PDF | PyMuPDF | Page-aware extraction |
| Workflows | LangGraph | Multi-step agent |
| App DB | SQLite | Document metadata |
| Containers | Docker + Docker Compose | Deployment |

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key ([get one free](https://console.groq.com/keys))

### 1. Clone & Configure

```bash
git clone <repo-url>
cd ResearchLens
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The first run will download the embedding model (~80MB).

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 4. Docker (Alternative)

```bash
# From project root
cp .env.example .env
# Edit .env with your GROQ_API_KEY

docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Health: http://localhost:8000/health

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/documents/upload` | Upload research PDF |
| GET | `/documents` | List uploaded documents |
| GET | `/documents/{id}` | Document details |
| DELETE | `/documents/{id}` | Delete document + vectors |
| POST | `/research/query` | Evidence-grounded Q&A |
| POST | `/research/analyze` | Structured paper analysis |
| POST | `/research/compare` | Multi-paper comparison |
| POST | `/research/verify-claim` | Claim verification |
| GET | `/health` | Health check |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | *required* | Groq API key |
| `LLM_MODEL` | llama-3.3-70b-versatile | Groq model |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Local embedding model |
| `MAX_UPLOAD_SIZE_MB` | 50 | Max upload size |
| `CHUNK_SIZE` | 512 | Chunk size in chars |
| `CHUNK_OVERLAP` | 50 | Overlap between chunks |
| `CORS_ORIGINS` | localhost:5173,3000 | Allowed CORS origins |
| `RATE_LIMIT_PER_MINUTE` | 30 | Rate limit per IP |

---

## Testing

```bash
cd backend
python -m pytest app/tests/ -v
```

### Manual Test Cases
1. Upload a real PDF → verify pages extracted correctly
2. Ask a question with a known answer → verify correct page citation
3. Ask a question with NO answer → verify "insufficient evidence" response
4. Upload 2+ papers → compare → verify per-paper citations
5. Submit a claim → check verdict matches paper content
6. Delete a document → verify gone from search results
7. Upload PDF with "Ignore previous instructions" → verify treated as data

---

## License

MIT

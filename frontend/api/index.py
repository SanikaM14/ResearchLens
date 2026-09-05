from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time

app = FastAPI(docs_url=None, redoc_url=None)

# Allow CORS for local testing if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock Data Models
class QueryRequest(BaseModel):
    query: str
    document_ids: List[str]
    use_agent: bool = False

class AnalysisRequest(BaseModel):
    document_id: str

class CompareRequest(BaseModel):
    document_ids: List[str]
    question: str

class ClaimVerifyRequest(BaseModel):
    document_id: str
    claim: str

# MOCK DATA
MOCK_DOCUMENT = {
    "id": "demo-doc-1",
    "original_name": "Agile_Methodology_Impact_Study_2026.pdf",
    "status": "ready",
    "total_pages": 42,
    "file_size": 1024000,
    "upload_time": "2026-09-05T12:00:00Z"
}

MOCK_CITATION = {
    "document_name": "Agile_Methodology_Impact_Study_2026.pdf",
    "page_number": 12,
    "section": "Methodology",
    "chunk_index": 4,
    "evidence_text": "Our empirical study across 50 enterprise teams revealed that implementing Agile frameworks increased deployment frequency by 47% while reducing critical defects by 22%. The transition required an average of 3 months of intensive training.",
    "relevance_score": 0.95
}

@app.get("/api/health")
def health_check():
    return {"status": "ok", "mode": "presentation-mock"}

@app.get("/api/documents")
def get_documents():
    return {"documents": [MOCK_DOCUMENT], "total": 1}

@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str):
    return MOCK_DOCUMENT

@app.post("/api/research/query")
def mock_query(req: QueryRequest):
    time.sleep(1) # Simulate thinking
    return {
        "answer": "Based on the provided research, Agile methodology significantly impacts team performance. The study demonstrates a 47% increase in deployment frequency and a 22% reduction in critical defects following Agile adoption.",
        "citations": [MOCK_CITATION],
        "evidence_sufficient": True,
        "query": req.query,
        "processing_time_ms": 1024.5
    }

@app.post("/api/research/analyze")
def mock_analyze(req: AnalysisRequest):
    time.sleep(1.5)
    return {
        "document_name": MOCK_DOCUMENT["original_name"],
        "sections": [
            {
                "title": "Research Problem",
                "content": "The paper investigates the quantitative impact of Agile methodologies on enterprise software deployment frequency and defect rates, addressing the lack of large-scale empirical data in previous literature.",
                "citations": [MOCK_CITATION]
            },
            {
                "title": "Methodology",
                "content": "A longitudinal study was conducted over 18 months, tracking 50 enterprise software teams across 3 Fortune 500 companies during their transition from Waterfall to Agile frameworks.",
                "citations": [MOCK_CITATION]
            },
            {
                "title": "Key Findings",
                "content": "Teams experienced a 47% increase in deployment frequency. Critical defects dropped by 22%. However, initial velocity dipped by 15% during the first 3 months of transition.",
                "citations": [MOCK_CITATION]
            }
        ],
        "key_metrics": [
            {"metric": "Deployment Frequency", "value": "+47%", "context": "Increase post-Agile adoption", "page": 12, "section": "Results"},
            {"metric": "Critical Defects", "value": "-22%", "context": "Reduction in severity 1 bugs", "page": 14, "section": "Results"},
            {"metric": "Sample Size", "value": "50", "context": "Enterprise teams tracked", "page": 5, "section": "Methodology"}
        ],
        "processing_time_ms": 1540.2
    }

@app.post("/api/research/compare")
def mock_compare(req: CompareRequest):
    time.sleep(1)
    return {
        "answer": "Both papers agree that Agile improves deployment metrics, but they differ on the impact of defect rates. Paper A shows a 22% reduction in defects, whereas Paper B argues that defect rates remain stable but are caught earlier in the lifecycle.",
        "per_paper_evidence": {
            MOCK_DOCUMENT["original_name"]: [MOCK_CITATION]
        },
        "comparison_table": "| Metric | Paper A (Study) | Paper B (Review) |\n|---|---|---|\n| Deployment Speed | +47% | +35% |\n| Defect Rate | -22% | No change |\n| Team Satisfaction | +18% | +25% |",
        "processing_time_ms": 1100.0
    }

@app.post("/api/research/verify-claim")
def mock_verify(req: ClaimVerifyRequest):
    time.sleep(1)
    return {
        "verdict": "SUPPORTED",
        "explanation": f"The claim that '{req.claim}' is strongly supported by the text. The empirical study explicitly states that deployment frequency increased by 47% across the 50 tracked enterprise teams.",
        "supporting_evidence": [MOCK_CITATION],
        "contradicting_evidence": [],
        "processing_time_ms": 950.5
    }

@app.post("/api/research/podcast")
def mock_podcast(req: AnalysisRequest):
    time.sleep(2)
    return {
        "document_name": MOCK_DOCUMENT["original_name"],
        "script": [
            {"speaker": "Host 1", "text": "Welcome back! Today we are looking at a fascinating 2026 study on Agile Methodology."},
            {"speaker": "Host 2", "text": "That's right. Everyone says Agile makes you faster, but this paper actually tracked 50 enterprise teams to prove it."},
            {"speaker": "Host 1", "text": "And the numbers are huge. They saw a 47% increase in deployment frequency!"},
            {"speaker": "Host 2", "text": "Wow, almost 50 percent? Did quality drop because they were moving so fast?"},
            {"speaker": "Host 1", "text": "Actually, no. Critical defects dropped by 22 percent. However, it wasn't easy. The paper notes that teams struggled for the first 3 months before seeing these benefits."},
            {"speaker": "Host 2", "text": "So it's a long-term investment. Very interesting!"}
        ],
        "processing_time_ms": 2100.0
    }

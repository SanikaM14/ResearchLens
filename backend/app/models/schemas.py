from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    id: str
    original_name: str
    status: str
    total_pages: Optional[int]
    file_size: Optional[int]
    upload_time: datetime

class DocumentListItem(BaseModel):
    id: str
    original_name: str
    status: str
    total_pages: Optional[int]
    file_size: Optional[int]
    upload_time: datetime

class DocumentDetail(BaseModel):
    id: str
    original_name: str
    status: str
    total_pages: Optional[int]
    file_size: Optional[int]
    upload_time: datetime
    file_hash: Optional[str]

class DocumentListResponse(BaseModel):
    documents: List[DocumentListItem]
    total: int

class CitationModel(BaseModel):
    document_name: str
    page_number: int
    section: Optional[str] = None
    chunk_index: int
    evidence_text: str
    relevance_score: Optional[float] = None

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    document_ids: List[str] = Field(..., min_length=1)
    use_agent: bool = False

class QueryResponse(BaseModel):
    answer: str
    citations: List[CitationModel]
    evidence_sufficient: bool
    query: str
    processing_time_ms: float

class AnalysisSection(BaseModel):
    title: str
    content: str
    citations: List[CitationModel]

class AnalysisRequest(BaseModel):
    document_id: str

class AnalysisResponse(BaseModel):
    document_name: str
    sections: List[AnalysisSection]
    key_metrics: List[dict]
    processing_time_ms: float

class CompareRequest(BaseModel):
    document_ids: List[str] = Field(..., min_length=2, max_length=5)
    question: str

class CompareResponse(BaseModel):
    answer: str
    per_paper_evidence: Dict[str, List[CitationModel]]
    comparison_table: Optional[str] = None
    processing_time_ms: float

class ClaimVerifyRequest(BaseModel):
    document_id: str
    claim: str = Field(..., min_length=10, max_length=2000)

class ClaimVerifyResponse(BaseModel):
    verdict: Literal['SUPPORTED', 'PARTIALLY_SUPPORTED', 'NOT_CLEARLY_SUPPORTED']
    explanation: str
    supporting_evidence: List[CitationModel]
    contradicting_evidence: List[CitationModel]
    processing_time_ms: float

class HealthResponse(BaseModel):
    status: str
    version: str
    documents_count: int
    vector_store_status: str

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

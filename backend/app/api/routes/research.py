"""
Research API routes for ResearchLens.
Handles evidence-grounded Q&A, structured analysis, multi-paper comparison, and claim verification.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db, Document, DocumentStatus
from app.core.security import validate_document_id, sanitize_query
from app.models.schemas import (
    QueryRequest, QueryResponse,
    AnalysisRequest, AnalysisResponse,
    CompareRequest, CompareResponse,
    ClaimVerifyRequest, ClaimVerifyResponse,
)
from app.services.retrieval_service import (
    answer_question,
    analyze_document,
    compare_papers,
    verify_claim,
    create_podcast,
)
from pydantic import BaseModel
from typing import List, Dict, Any

class PodcastResponse(BaseModel):
    document_name: str
    script: List[Dict[str, str]]
    processing_time_ms: float

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["research"])


async def _validate_document_exists(doc_id: str, db: AsyncSession) -> Document:
    """Validate that a document exists and is ready for querying."""
    validate_document_id(doc_id)
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document not found.")
    if doc.status != DocumentStatus.ready:
        raise HTTPException(
            status_code=400,
            detail=f"Document '{doc.original_name}' is not ready. Current status: {doc.status.value}."
        )
    return doc


@router.post("/query", response_model=QueryResponse)
async def research_query(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Ask an evidence-grounded question about uploaded research papers.
    Returns an answer with citations from metadata — never invented by the LLM.
    """
    # Validate all document IDs exist and are ready
    for doc_id in request.document_ids:
        await _validate_document_exists(doc_id, db)
    
    query = sanitize_query(request.query)
    
    try:
        if request.use_agent:
            # Use LangGraph workflow for complex queries
            from app.workflows.research_graph import run_research_workflow
            result = run_research_workflow(query, request.document_ids)
            
            from app.models.schemas import CitationModel
            citations = [CitationModel(**c) for c in result.get("citations", [])]
            
            return QueryResponse(
                answer=result.get("answer", ""),
                citations=citations,
                evidence_sufficient=len(citations) > 0,
                query=query,
                processing_time_ms=result.get("processing_time_ms", 0),
            )
        else:
            return answer_question(query, request.document_ids)
    except Exception as e:
        logger.error(f"Research query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. Please try again."
        )


@router.post("/analyze", response_model=AnalysisResponse)
async def research_analyze(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a structured analysis of a research paper.
    Extracts: research problem, methodology, findings, metrics, limitations, future work.
    """
    doc = await _validate_document_exists(request.document_id, db)
    
    try:
        return analyze_document(request.document_id, doc.original_name)
    except Exception as e:
        logger.error(f"Analysis failed for document {request.document_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during paper analysis. Please try again."
        )


@router.post("/compare", response_model=CompareResponse)
async def research_compare(request: CompareRequest, db: AsyncSession = Depends(get_db)):
    """
    Compare multiple research papers with per-paper evidence and citations.
    Sources are never mixed — every claim is attributed to its specific paper.
    """
    for doc_id in request.document_ids:
        await _validate_document_exists(doc_id, db)
    
    query = sanitize_query(request.question)
    
    try:
        return compare_papers(request.document_ids, query)
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during paper comparison. Please try again."
        )


@router.post("/verify-claim", response_model=ClaimVerifyResponse)
async def research_verify_claim(request: ClaimVerifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify whether a specific claim is supported by the research paper.
    Returns SUPPORTED, PARTIALLY_SUPPORTED, or NOT_CLEARLY_SUPPORTED with evidence.
    """
    doc = await _validate_document_exists(request.document_id, db)
    query = sanitize_query(request.claim)
    
    try:
        return verify_claim(request.document_id, query, doc.original_name)
    except Exception as e:
        logger.error(f"Claim verification failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during claim verification. Please try again."
        )

@router.post("/podcast", response_model=PodcastResponse)
async def research_podcast(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a 2-speaker podcast script based on a research paper.
    """
    doc = await _validate_document_exists(request.document_id, db)
    
    try:
        return create_podcast(request.document_id, doc.original_name)
    except Exception as e:
        logger.error(f"Podcast generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during podcast generation. Please try again."
        )

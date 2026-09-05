"""
Research API routes for ResearchLens.
Handles evidence-grounded Q&A, structured analysis, multi-paper comparison, and claim verification.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db, Document, DocumentStatus, User
from app.api.routes.auth import get_current_user
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
    audio_url: Optional[str] = None
    processing_time_ms: float

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["research"])


async def _validate_document_exists(doc_id: str, db: AsyncSession, current_user: User) -> Document:
    """Validate that a document exists, belongs to the user, and is ready for querying."""
    validate_document_id(doc_id)
    doc = await db.get(Document, doc_id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"Document not found.")
    if doc.status != DocumentStatus.ready:
        raise HTTPException(
            status_code=400,
            detail=f"Document '{doc.original_name}' is not ready. Current status: {doc.status.value}."
        )
    return doc


from app.core.limiter import limiter
from fastapi import Request

@router.post("/query", response_model=QueryResponse)
@limiter.limit("20/minute")
async def research_query(request_obj: Request, request: QueryRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Ask an evidence-grounded question about uploaded research papers.
    Returns an answer with citations from metadata — never invented by the LLM.
    """
    # Validate all document IDs exist and are ready
    for doc_id in request.document_ids:
        await _validate_document_exists(doc_id, db, current_user)
    
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
            return await answer_question(query, request.document_ids)
    except Exception as e:
        logger.error(f"Research query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. Please try again."
        )


@router.post("/analyze", response_model=AnalysisResponse)
async def research_analyze(request: AnalysisRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Generate a structured analysis of a research paper.
    Extracts: research problem, methodology, findings, metrics, limitations, future work.
    """
    doc = await _validate_document_exists(request.document_id, db, current_user)
    
    try:
        return await analyze_document(request.document_id, doc.original_name)
    except Exception as e:
        logger.error(f"Analysis failed for document {request.document_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during paper analysis. Please try again."
        )


@router.post("/compare", response_model=CompareResponse)
async def research_compare(request: CompareRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Compare multiple research papers with per-paper evidence and citations.
    Sources are never mixed — every claim is attributed to its specific paper.
    """
    for doc_id in request.document_ids:
        await _validate_document_exists(doc_id, db, current_user)
    
    query = sanitize_query(request.question)
    
    try:
        return await compare_papers(request.document_ids, query)
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during paper comparison. Please try again."
        )


@router.post("/verify-claim", response_model=ClaimVerifyResponse)
async def research_verify_claim(request: ClaimVerifyRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Verify whether a specific claim is supported by the research paper.
    Returns SUPPORTED, PARTIALLY_SUPPORTED, or NOT_CLEARLY_SUPPORTED with evidence.
    """
    doc = await _validate_document_exists(request.document_id, db, current_user)
    query = sanitize_query(request.claim)
    
    try:
        return await verify_claim(request.document_id, query, doc.original_name)
    except Exception as e:
        logger.error(f"Claim verification failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during claim verification. Please try again."
        )

import os
import edge_tts

@router.post("/podcast", response_model=PodcastResponse)
async def research_podcast(request: AnalysisRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Generate a 2-speaker podcast script based on a research paper and synthesize audio.
    """
    doc = await _validate_document_exists(request.document_id, db, current_user)
    
    try:
        result = await create_podcast(request.document_id, doc.original_name)
        script = result.get("script", [])
        
        audio_filename = f"podcast_{request.document_id}.mp3"
        audio_path = os.path.join("uploads", audio_filename)
        
        # Synthesize audio if not already generated
        if script and not os.path.exists(audio_path):
            with open(audio_path, "wb") as f:
                for turn in script:
                    voice = "en-US-ChristopherNeural" if turn.get("speaker") == "Host 1" else "en-US-JennyNeural"
                    communicate = edge_tts.Communicate(turn.get("text", ""), voice)
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                            
        result["audio_url"] = f"/uploads/{audio_filename}"
        return result
    except Exception as e:
        logger.error(f"Podcast generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during podcast generation. Please try again."
        )

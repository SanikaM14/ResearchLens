"""
Health check endpoint for ResearchLens.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.core.database import get_db, Document
from app.models.schemas import HealthResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Application health check.
    Returns status, version, document count, and vector store connectivity.
    """
    # Count documents in SQLite
    try:
        result = await db.execute(select(func.count()).select_from(Document))
        doc_count = result.scalar() or 0
    except Exception:
        doc_count = -1
    
    # Check ChromaDB connectivity
    try:
        from app.services.vector_store_service import get_collection_stats
        stats = get_collection_stats()
        vector_status = f"connected ({stats.get('total_vectors', 0)} vectors)"
    except Exception as e:
        vector_status = "disconnected"
        logger.warning(f"Vector store health check failed: {e}")
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        documents_count=doc_count,
        vector_store_status=vector_status,
    )

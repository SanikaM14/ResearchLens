"""
Document management API routes for ResearchLens.
Handles PDF upload with validation, ingestion pipeline, listing, and deletion.
"""
import os
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db, Document, DocumentStatus, AsyncSessionLocal
from app.core.security import validate_pdf_file, generate_safe_filename, compute_file_hash, validate_document_id
from app.core.config import get_settings
from app.models.schemas import DocumentUploadResponse, DocumentListItem, DocumentListResponse, DocumentDetail
from app.services.pdf_service import extract_text_by_page, validate_pdf
from app.services.chunking_service import chunk_document
from app.services.vector_store_service import add_document_chunks, delete_document_vectors, get_document_chunk_count
import aiofiles

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


async def _process_document(doc_id: str, file_path: str, original_name: str):
    """
    Background task: extract text, chunk, embed, and store in ChromaDB.
    Updates document status in SQLite on success or failure.
    """
    settings = get_settings()
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Validate the PDF is readable
            pdf_info = validate_pdf(file_path)
            if not pdf_info["is_valid"]:
                raise ValueError(f"Invalid PDF: {pdf_info['error']}")
            
            # 2. Extract text page by page
            pages = extract_text_by_page(file_path)
            
            if not pages or all(p.is_empty for p in pages):
                raise ValueError("PDF contains no extractable text.")
            
            # 3. Compute file hash for deduplication
            file_hash = compute_file_hash(file_path)
            
            # 4. Chunk text with metadata preservation
            chunks = chunk_document(
                pages=pages,
                document_id=doc_id,
                document_name=original_name,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            
            if not chunks:
                raise ValueError("No meaningful text chunks could be extracted from the PDF.")
            
            # 5. Store chunks in ChromaDB (embeddings generated automatically)
            add_document_chunks(doc_id, chunks)
            
            # 6. Update document status to ready
            doc = await db.get(Document, doc_id)
            if doc:
                doc.status = DocumentStatus.ready
                doc.total_pages = len(pages)
                doc.file_hash = file_hash
                doc.error_message = None
                await db.commit()
                logger.info(
                    f"Document '{original_name}' processed: "
                    f"{len(pages)} pages, {len(chunks)} chunks indexed."
                )
        
        except Exception as e:
            logger.error(f"Document processing failed for '{original_name}': {e}")
            try:
                doc = await db.get(Document, doc_id)
                if doc:
                    doc.status = DocumentStatus.failed
                    doc.error_message = str(e)[:500]  # Truncate long errors
                    await db.commit()
            except Exception:
                logger.error(f"Failed to update document status for {doc_id}")


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and ingest a research paper PDF.
    
    - Validates file type, magic bytes, and size
    - Saves with UUID-based safe filename (never uses original filename as path)
    - Triggers background processing: extraction → chunking → embedding → ChromaDB
    """
    settings = get_settings()
    
    # Validate the uploaded file
    validate_pdf_file(file)
    
    # Generate safe filename
    safe_filename = generate_safe_filename(file.filename)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Stream file to disk with size enforcement
    file_size = 0
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                if file_size > max_bytes:
                    # Clean up partial file
                    await out_file.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB}MB."
                    )
                await out_file.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed. Please try again.")
    
    # Create document record
    doc = Document(
        original_name=file.filename,
        safe_filename=safe_filename,
        file_size=file_size,
        status=DocumentStatus.processing,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    # Trigger background processing
    background_tasks.add_task(_process_document, doc.id, file_path, doc.original_name)
    
    return DocumentUploadResponse(
        id=doc.id,
        original_name=doc.original_name,
        status=doc.status.value,
        total_pages=None,
        file_size=doc.file_size,
        upload_time=doc.upload_time,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all uploaded documents with their ingestion status."""
    result = await db.execute(select(Document).order_by(Document.upload_time.desc()))
    docs = result.scalars().all()
    
    items = [
        DocumentListItem(
            id=d.id,
            original_name=d.original_name,
            status=d.status.value,
            total_pages=d.total_pages,
            file_size=d.file_size,
            upload_time=d.upload_time,
        )
        for d in docs
    ]
    
    return DocumentListResponse(documents=items, total=len(items))


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed metadata for a specific document."""
    validate_document_id(document_id)
    
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    return DocumentDetail(
        id=doc.id,
        original_name=doc.original_name,
        status=doc.status.value,
        total_pages=doc.total_pages,
        file_size=doc.file_size,
        upload_time=doc.upload_time,
        file_hash=doc.file_hash,
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a document and all associated data:
    - Remove PDF file from disk
    - Remove all vector embeddings from ChromaDB
    - Remove metadata from SQLite
    """
    validate_document_id(document_id)
    
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    settings = get_settings()
    
    # 1. Delete file from disk
    file_path = os.path.join(settings.UPLOAD_DIR, doc.safe_filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            logger.warning(f"Could not delete file {file_path}: {e}")
    
    # 2. Delete vectors from ChromaDB
    try:
        delete_document_vectors(document_id)
    except Exception as e:
        logger.warning(f"Could not delete vectors for {document_id}: {e}")
    
    # 3. Delete from SQLite
    await db.delete(doc)
    await db.commit()
    
    logger.info(f"Document '{doc.original_name}' (ID: {document_id}) deleted successfully.")
    return {"message": "Document deleted successfully.", "document_id": document_id}

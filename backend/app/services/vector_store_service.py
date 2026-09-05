import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from app.core.config import get_settings
from typing import List, Dict, Any
from app.services.chunking_service import ChunkMetadata

_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _chroma_client

def get_collection():
    client = get_chroma_client()
    settings = get_settings()
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=settings.EMBEDDING_MODEL)
    collection = client.get_or_create_collection(name="research_docs", embedding_function=emb_fn)
    return collection

def add_document_chunks(document_id: str, chunks: List[ChunkMetadata]) -> None:
    collection = get_collection()
    ids = [f"{document_id}_{c.chunk_index}" for c in chunks]
    documents = [c.text for c in chunks]
    metadatas = [{
        "document_id": c.document_id,
        "document_name": c.document_name,
        "page_number": c.page_number,
        "section": c.section,
        "chunk_index": c.chunk_index
    } for c in chunks]
    
    # batch insertion to avoid payload too large issues if needed, but assuming chromadb handles it
    collection.add(ids=ids, documents=documents, metadatas=metadatas)

def search_similar(query_embedding: List[float], document_ids: List[str], top_k: int = 10) -> Dict[str, Any]:
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"document_id": {"$in": document_ids}}
    )
    return results

def search_by_text(query_text: str, document_ids: List[str], top_k: int = 10) -> Dict[str, Any]:
    collection = get_collection()
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        where={"document_id": {"$in": document_ids}}
    )
    return results

def delete_document_vectors(document_id: str) -> None:
    collection = get_collection()
    collection.delete(where={"document_id": document_id})

def get_document_chunk_count(document_id: str) -> int:
    collection = get_collection()
    results = collection.get(where={"document_id": document_id}, include=[])
    return len(results.get('ids', []))

def get_collection_stats() -> Dict[str, Any]:
    collection = get_collection()
    return {"total_vectors": collection.count()}

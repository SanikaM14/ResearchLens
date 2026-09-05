import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from app.core.config import get_settings
from typing import List, Dict, Any
from app.services.chunking_service import ChunkMetadata
import heapq

_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _chroma_client

def get_collection(document_id: str):
    client = get_chroma_client()
    settings = get_settings()
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=settings.EMBEDDING_MODEL)
    collection_name = f"doc_{document_id.replace('-', '_')}"
    collection = client.get_or_create_collection(name=collection_name, embedding_function=emb_fn)
    return collection

def add_document_chunks(document_id: str, chunks: List[ChunkMetadata]) -> None:
    collection = get_collection(document_id)
    ids = [f"{document_id}_{c.chunk_index}" for c in chunks]
    documents = [c.text for c in chunks]
    metadatas = [{
        "document_id": c.document_id,
        "document_name": c.document_name,
        "page_number": c.page_number,
        "section": c.section,
        "chunk_index": c.chunk_index
    } for c in chunks]
    
    collection.add(ids=ids, documents=documents, metadatas=metadatas)

def _merge_results(all_results: List[Dict[str, Any]], top_k: int) -> Dict[str, Any]:
    merged = {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}
    flattened = []
    
    for res in all_results:
        if not res or not res.get("ids") or not res["ids"][0]:
            continue
            
        for i in range(len(res["ids"][0])):
            flattened.append({
                "id": res["ids"][0][i],
                "distance": res["distances"][0][i] if "distances" in res and res["distances"] else 0.0,
                "metadata": res["metadatas"][0][i] if "metadatas" in res and res["metadatas"] else {},
                "document": res["documents"][0][i] if "documents" in res and res["documents"] else ""
            })
            
    # Sort by distance ascending (lower is better for cosine distance in Chroma)
    flattened.sort(key=lambda x: x["distance"])
    top_results = flattened[:top_k]
    
    for item in top_results:
        merged["ids"][0].append(item["id"])
        merged["distances"][0].append(item["distance"])
        merged["metadatas"][0].append(item["metadata"])
        merged["documents"][0].append(item["document"])
        
    return merged

def search_similar(query_embedding: List[float], document_ids: List[str], top_k: int = 10) -> Dict[str, Any]:
    all_results = []
    for doc_id in document_ids:
        try:
            col = get_collection(doc_id)
            res = col.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            all_results.append(res)
        except Exception:
            pass
    return _merge_results(all_results, top_k)

def search_by_text(query_text: str, document_ids: List[str], top_k: int = 10) -> Dict[str, Any]:
    all_results = []
    for doc_id in document_ids:
        try:
            col = get_collection(doc_id)
            res = col.query(
                query_texts=[query_text],
                n_results=top_k
            )
            all_results.append(res)
        except Exception:
            pass
    return _merge_results(all_results, top_k)

def delete_document_vectors(document_id: str) -> None:
    client = get_chroma_client()
    collection_name = f"doc_{document_id.replace('-', '_')}"
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

def get_document_chunk_count(document_id: str) -> int:
    try:
        col = get_collection(document_id)
        results = col.get(include=[])
        return len(results.get('ids', []))
    except Exception:
        return 0

def get_collection_stats() -> Dict[str, Any]:
    # We can't easily get total vectors across all collections efficiently without iterating.
    # We'll just return a placeholder or sum them up.
    client = get_chroma_client()
    total = sum(col.count() for col in client.list_collections())
    return {"total_vectors": total}

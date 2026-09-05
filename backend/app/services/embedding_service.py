from sentence_transformers import SentenceTransformer
from app.core.config import get_settings
from typing import List

_model_instance = None

def get_embedding_model():
    global _model_instance
    if _model_instance is None:
        settings = get_settings()
        try:
            _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {e}")
    return _model_instance

def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()

def embed_query(query: str) -> List[float]:
    model = get_embedding_model()
    embedding = model.encode([query], normalize_embeddings=True)
    return embedding[0].tolist()

def get_embedding_dimension() -> int:
    model = get_embedding_model()
    return model.get_sentence_embedding_dimension()

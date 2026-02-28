"""
Embedder — text → vector representations.
Stub for Day 1; fully implemented in Day 2.
"""
from typing import List

from core.config import settings


class Embedder:
    """
    Wraps a sentence-transformers model to produce embedding vectors.
    Default model: all-MiniLM-L6-v2 (fast, local, no API cost).
    Configurable via EMBEDDING_MODEL env var to swap in OpenAI or Anthropic embeddings.
    """

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None  # lazy-loaded in Day 2

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return normalized embedding vectors for a list of texts."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model.encode(texts, normalize_embeddings=True).tolist()

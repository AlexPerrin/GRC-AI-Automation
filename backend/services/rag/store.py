"""
VectorStore — ChromaDB wrapper for document chunk storage and retrieval.
Stub for Day 1; fully implemented in Day 2.
"""
from typing import List

from core.config import settings


class VectorStore:
    """
    Wraps ChromaDB in embedded (no-server) persistent mode.
    Collection naming convention:
      - Vendor documents:    vendor_{vendor_id}_{stage}_{doc_id}
      - Knowledge base:      kb_legal  /  kb_security
    """

    def __init__(self, persist_dir: str = settings.CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        self._client = None  # lazy-loaded in Day 2

    def upsert_chunks(self, collection_name: str, chunks) -> None:
        """Store or update chunks in the named collection. Implemented Day 2."""
        raise NotImplementedError

    def query(self, collection_name: str, query_text: str, n_results: int = 5) -> List[str]:
        """Return the top-n most relevant chunk texts. Implemented Day 2."""
        raise NotImplementedError

    def collection_exists(self, collection_name: str) -> bool:
        """Check whether a collection has been seeded. Implemented Day 2."""
        raise NotImplementedError

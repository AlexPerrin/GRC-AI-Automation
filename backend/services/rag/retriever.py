"""
Retriever — query → formatted context string for prompt injection.
Stub for Day 1; fully implemented in Day 2.
"""
from services.rag.store import VectorStore


class Retriever:
    """
    High-level interface used by all AI analysis modules.
    Fetches the top-k relevant chunks and formats them for prompt injection.
    """

    def __init__(self, store: VectorStore):
        self.store = store

    def retrieve(self, query: str, collection: str, n: int = 5) -> str:
        """
        Return the top-n chunks from the named collection as a single
        newline-delimited string with chunk separators.
        Implemented Day 2.
        """
        chunks = self.store.query(collection, query, n)
        return "\n---\n".join(chunks)

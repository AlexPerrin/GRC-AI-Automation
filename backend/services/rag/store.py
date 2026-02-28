"""
VectorStore — ChromaDB wrapper for document chunk storage and retrieval.

In Docker:  connects to the chromadb service via HttpClient (CHROMA_HOST/PORT).
Locally:    uses PersistentClient with a local directory (CHROMA_PERSIST_DIR).

The correct client is selected automatically via settings.chroma_use_server.
Fully implemented in Day 2.
"""
from typing import List

from core.config import settings
from services.rag.embedder import Embedder

_embedder = Embedder()


class VectorStore:
    """
    Wraps ChromaDB and selects the right client based on configuration:

      Docker / server mode  →  chromadb.HttpClient(host, port)
      Local / embedded mode →  chromadb.PersistentClient(path)

    Collection naming convention:
      - Vendor documents:  vendor_{vendor_id}_{stage}_{doc_id}
      - Knowledge base:    kb_legal  /  kb_security
    """

    def __init__(self):
        self._client = None  # lazy-loaded in Day 2

    def _get_client(self):
        """Return (and cache) the appropriate ChromaDB client."""
        if self._client is None:
            import chromadb
            if settings.chroma_use_server:
                self._client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,
                )
            else:
                self._client = chromadb.PersistentClient(
                    path=settings.CHROMA_PERSIST_DIR,
                )
        return self._client

    def upsert_chunks(self, collection_name: str, chunks) -> None:
        """Store or update chunks in the named collection."""
        client = self._get_client()
        col = client.get_or_create_collection(collection_name)
        texts = [c.text for c in chunks]
        embeddings = _embedder.embed(texts)
        col.upsert(
            ids=[f"{collection_name}_{i}" for i in range(len(chunks))],
            embeddings=embeddings,
            documents=texts,
            metadatas=[c.metadata for c in chunks],
        )

    def query(self, collection_name: str, query_text: str, n_results: int = 5) -> List[str]:
        """Return the top-n most relevant chunk texts."""
        client = self._get_client()
        col = client.get_or_create_collection(collection_name)
        embedding = _embedder.embed([query_text])
        results = col.query(query_embeddings=embedding, n_results=n_results)
        return results["documents"][0]

    def collection_exists(self, collection_name: str) -> bool:
        """Check whether a collection has been seeded."""
        client = self._get_client()
        # ChromaDB v0.6.0+: list_collections() returns collection names directly
        names = list(client.list_collections())
        return collection_name in names

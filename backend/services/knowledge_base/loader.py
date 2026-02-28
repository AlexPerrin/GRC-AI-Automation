"""
KnowledgeBaseLoader — seeds kb_legal and kb_security ChromaDB collections on startup.
Stub for Day 1; fully implemented in Day 2.
"""
from services.document.chunker import DocumentChunker
from services.knowledge_base.legal_kb import LEGAL_KB_ENTRIES
from services.knowledge_base.security_kb import SECURITY_KB_ENTRIES
from services.rag.embedder import Embedder
from services.rag.store import VectorStore


class KnowledgeBaseLoader:
    """
    Checks whether the knowledge base collections exist in ChromaDB.
    If absent, chunks, embeds, and upserts all entries.
    This is a one-time operation — subsequent startups are a no-op.
    """

    def __init__(self, store: VectorStore | None = None):
        self.store = store or VectorStore()

    async def seed_if_empty(self) -> None:
        """Seed kb_legal and kb_security if not already present."""
        chunker = DocumentChunker()
        for collection, entries in [
            ("kb_legal", LEGAL_KB_ENTRIES),
            ("kb_security", SECURITY_KB_ENTRIES),
        ]:
            if not self.store.collection_exists(collection):
                chunks = []
                for entry in entries:
                    for c in chunker.chunk(entry["text"], {**entry["metadata"], "entry_id": entry["id"]}):
                        chunks.append(c)
                self.store.upsert_chunks(collection, chunks)

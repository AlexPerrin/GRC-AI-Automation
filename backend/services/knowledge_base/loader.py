"""
KnowledgeBaseLoader — seeds kb_legal and kb_security ChromaDB collections on startup.
Stub for Day 1; fully implemented in Day 2.
"""
from services.knowledge_base.legal_kb import LEGAL_KB_ENTRIES
from services.knowledge_base.security_kb import SECURITY_KB_ENTRIES
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
        """Seed kb_legal and kb_security if not already present. Implemented Day 2."""
        # Day 2 will implement:
        #   if not self.store.collection_exists("kb_legal"):
        #       <embed and upsert LEGAL_KB_ENTRIES>
        #   if not self.store.collection_exists("kb_security"):
        #       <embed and upsert SECURITY_KB_ENTRIES>
        pass

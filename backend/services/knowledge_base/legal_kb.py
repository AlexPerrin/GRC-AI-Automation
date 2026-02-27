"""
Legal / Regulatory Knowledge Base entries.
Each entry maps a regulatory requirement to a structured description.
Seeded into ChromaDB collection 'kb_legal' on first startup.
Stub for Day 1; content populated in Day 2.
"""

LEGAL_KB_ENTRIES: list[dict] = [
    # Format: {"id": str, "text": str, "metadata": {"regulation": str, "jurisdiction": str, "article": str}}
    # Populated during Day 2 with GDPR, PIPEDA, CPPA, HIPAA, PCI DSS entries.
]

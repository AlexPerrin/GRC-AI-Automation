"""
Security Controls Knowledge Base entries.
Maps control domains (NIST CSF, SOC 2 TSC, ISO 27001) to requirement descriptions.
Seeded into ChromaDB collection 'kb_security' on first startup.
Stub for Day 1; content populated in Day 2.
"""

SECURITY_KB_ENTRIES: list[dict] = [
    # Format: {"id": str, "text": str, "metadata": {"framework": str, "domain": str, "control_id": str}}
    # Populated during Day 2 with access_control, data_protection,
    # incident_response, vulnerability_management, business_continuity,
    # and supply_chain domain entries.
]

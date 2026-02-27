"""
SecurityAnalyzer — Stage 3 RAG-powered security risk evaluation module.
Stub for Day 1; fully implemented in Day 4.
"""
from services.llm.client import LLMClient
from services.rag.retriever import Retriever

# Retrieval queries per control domain — tuned during Day 4 RAG quality check.
SECURITY_RETRIEVAL_QUERIES: dict[str, str] = {
    "access_control": "MFA multi-factor authentication least privilege access management",
    "data_protection": "encryption at rest in transit key management data security",
    "incident_response": "incident response breach notification SLA detection",
    "vulnerability_management": "penetration testing patching vulnerability scanning CVE",
    "business_continuity": "disaster recovery RTO RPO backup business continuity",
    "supply_chain": "third party vendor assessment software composition supply chain",
}


class SecurityAnalysisResult:
    """Structured output from the security analysis module. Schema defined Day 4."""
    pass


class SecurityAnalyzer:
    """
    Retrieves control requirements from kb_security and relevant sections
    from the vendor's security documentation, then produces a domain-level
    risk report with scores, gap descriptions, and a risk disposition.

    NDA gate: raises PermissionError if vendor status is not SECURITY_REVIEW or later.
    """

    def __init__(self, llm: LLMClient, retriever: Retriever):
        self.llm = llm
        self.retriever = retriever

    async def analyze(self, vendor_id: int, doc_id: int) -> SecurityAnalysisResult:
        """Run RAG-grounded security analysis. Implemented Day 4."""
        raise NotImplementedError

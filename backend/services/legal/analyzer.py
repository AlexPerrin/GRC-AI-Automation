"""
LegalAnalyzer — Stage 2 RAG-powered legal and regulatory compliance module.
Fully implemented in Day 3.
"""
from __future__ import annotations

import dataclasses
import logging
from typing import Literal

from services.llm.client import LLMClient
from services.rag.retriever import Retriever

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retrieval queries — one per compliance domain
# ---------------------------------------------------------------------------

LEGAL_RETRIEVAL_QUERIES: dict[str, str] = {
    "data_privacy": (
        "personal data processing lawful basis consent privacy policy "
        "transparency GDPR PIPEDA CPPA"
    ),
    "data_security": (
        "encryption security safeguards technical organisational measures "
        "breach notification GDPR Art. 32 PIPEDA 4.7"
    ),
    "data_subject_rights": (
        "right access erasure portability rectification objection restriction "
        "GDPR Art. 13 PIPEDA 4.9"
    ),
    "processor_obligations": (
        "data processing agreement DPA sub-processor controller obligations "
        "audit rights GDPR Art. 28"
    ),
    "retention_deletion": (
        "data retention deletion disposal anonymisation storage limitation "
        "GDPR Art. 5 PCI DSS Req. 3"
    ),
    "cross_border_transfers": (
        "international data transfer standard contractual clauses adequacy "
        "third country GDPR PIPEDA"
    ),
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a legal and regulatory compliance analyst specialising in data privacy law.

Your task is to assess a vendor's compliance with applicable regulations based on:
1. Regulatory requirements retrieved from the knowledge base.
2. Excerpts from the vendor's own documentation.

You MUST output a single JSON object — no markdown fences, no commentary — with exactly this schema:

{
  "regulation_findings": [
    {
      "regulation": "<e.g. GDPR>",
      "article": "<e.g. Art. 28>",
      "status": "<compliant|partial|non_compliant|not_applicable>",
      "finding": "<1–3 sentence assessment>",
      "evidence": "<quoted text from vendor document OR 'No evidence found'>"
    }
  ],
  "overall_risk": "<low|medium|high|critical>",
  "recommendation": "<approve|approve_with_conditions|reject>",
  "summary": "<2–4 sentence overall assessment>",
  "conditions": ["<condition if approve_with_conditions, else empty list>"]
}

Risk / recommendation guidance:
- low    → approve
- medium → approve_with_conditions (list specific remediation steps in conditions)
- high   → approve_with_conditions or reject depending on severity
- critical → reject

Be specific. Cite article numbers and quote vendor text as evidence wherever possible."""

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
_RECOMMENDATION_ORDER = {"approve": 0, "approve_with_conditions": 1, "reject": 2}


@dataclasses.dataclass
class RegulationFinding:
    regulation: str
    article: str
    status: Literal["compliant", "partial", "non_compliant", "not_applicable"]
    finding: str
    evidence: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class LegalAnalysisResult:
    regulation_findings: list[RegulationFinding]
    overall_risk: Literal["low", "medium", "high", "critical"]
    recommendation: Literal["approve", "approve_with_conditions", "reject"]
    summary: str
    conditions: list[str]

    def to_dict(self) -> dict:
        return {
            "regulation_findings": [f.to_dict() for f in self.regulation_findings],
            "overall_risk": self.overall_risk,
            "recommendation": self.recommendation,
            "summary": self.summary,
            "conditions": self.conditions,
        }


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class LegalAnalyzer:
    """
    Retrieves applicable regulatory requirements from kb_legal, fetches
    relevant vendor document sections, and produces a compliance matrix
    with per-requirement findings, evidence citations, and an overall
    recommendation.
    """

    def __init__(self, llm: LLMClient, retriever: Retriever):
        self.llm = llm
        self.retriever = retriever

    async def analyze(self, vendor_id: int, doc_id: int) -> LegalAnalysisResult:
        """
        Run 6 domain-scoped RAG+LLM calls and aggregate into a single
        LegalAnalysisResult.

        JSONDecodeError from complete_with_json_output is intentionally NOT
        caught here — it propagates to WorkflowService which sets ReviewStatus.ERROR.
        """
        vendor_collection = f"vendor_{vendor_id}_LEGAL_{doc_id}"

        all_findings: list[RegulationFinding] = []
        domain_results: list[dict] = []

        for domain, query in LEGAL_RETRIEVAL_QUERIES.items():
            kb_context = self.retriever.retrieve(query, "kb_legal", n=3)

            try:
                vendor_context = self.retriever.retrieve(query, vendor_collection, n=3)
            except Exception:
                logger.warning(
                    "Could not retrieve vendor context for domain=%s collection=%s",
                    domain,
                    vendor_collection,
                )
                vendor_context = ""

            user_prompt = (
                f"## Compliance domain: {domain.replace('_', ' ').title()}\n\n"
                f"### Regulatory knowledge base excerpts\n{kb_context}\n\n"
                f"### Vendor document excerpts\n"
                + (vendor_context if vendor_context else "(No vendor document excerpts available)")
                + "\n\nAnalyse the vendor's compliance for this domain and return the JSON object."
            )

            raw_dict = await self.llm.complete_with_json_output(_SYSTEM_PROMPT, user_prompt)
            domain_results.append(raw_dict)

            for finding_dict in raw_dict.get("regulation_findings", []):
                all_findings.append(
                    RegulationFinding(
                        regulation=finding_dict.get("regulation", ""),
                        article=finding_dict.get("article", ""),
                        status=finding_dict.get("status", "not_applicable"),
                        finding=finding_dict.get("finding", ""),
                        evidence=finding_dict.get("evidence", "No evidence found"),
                    )
                )

        # Aggregate: worst-case risk and recommendation across all domains
        overall_risk = "low"
        recommendation = "approve"
        summary = ""
        all_conditions: list[str] = []

        for result in domain_results:
            risk = result.get("overall_risk", "low")
            rec = result.get("recommendation", "approve")

            if _RISK_ORDER.get(risk, 0) > _RISK_ORDER.get(overall_risk, 0):
                overall_risk = risk
                summary = result.get("summary", "")

            if _RECOMMENDATION_ORDER.get(rec, 0) > _RECOMMENDATION_ORDER.get(recommendation, 0):
                recommendation = rec

            all_conditions.extend(result.get("conditions", []))

        # Fallback summary if none was set (all domains were low risk)
        if not summary and domain_results:
            summary = domain_results[-1].get("summary", "")

        # Deduplicate conditions while preserving order
        seen: set[str] = set()
        deduped_conditions: list[str] = []
        for c in all_conditions:
            if c not in seen:
                seen.add(c)
                deduped_conditions.append(c)

        return LegalAnalysisResult(
            regulation_findings=all_findings,
            overall_risk=overall_risk,  # type: ignore[arg-type]
            recommendation=recommendation,  # type: ignore[arg-type]
            summary=summary,
            conditions=deduped_conditions,
        )

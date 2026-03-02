"""
FinancialAnalyzer — Stage 4 RAG-powered financial risk assessment module.
Follows the same pattern as LegalAnalyzer and SecurityAnalyzer.
"""
from __future__ import annotations

import dataclasses
import logging
from typing import Literal

from services.llm.client import LLMClient
from services.rag.retriever import Retriever

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retrieval queries — one per financial assessment domain
# ---------------------------------------------------------------------------

FINANCIAL_RETRIEVAL_QUERIES: dict[str, str] = {
    "revenue_and_scale": (
        "annual revenue turnover financial statements gross profit business scale "
        "vendor size revenue growth year-over-year"
    ),
    "profitability": (
        "net income EBITDA operating profit profit margin profitability "
        "earnings financial performance operating expenses"
    ),
    "debt_and_leverage": (
        "debt ratio leverage long-term liabilities credit facility borrowing "
        "debt-to-equity solvency balance sheet liabilities"
    ),
    "liquidity_and_cash_flow": (
        "current ratio cash flow working capital liquidity quick ratio "
        "cash reserves operating cash flow short-term obligations"
    ),
    "concentration_risk": (
        "customer concentration revenue dependency major clients key accounts "
        "single customer risk revenue diversification"
    ),
    "insurance_and_governance": (
        "insurance coverage professional indemnity liability insurance audited accounts "
        "regulatory compliance governance financial controls audit"
    ),
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a financial risk analyst specialising in vendor due diligence.

Your task is to assess a vendor's financial health and risk profile based on:
1. Financial risk assessment frameworks retrieved from the knowledge base.
2. Excerpts from the vendor's own financial documentation.

You MUST output a single JSON object — no markdown fences, no commentary — with exactly this schema:

{
  "findings": [
    {
      "category": "<e.g. Annual Revenue>",
      "value": "<e.g. $10M or 'Not disclosed'>",
      "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
      "notes": "<1–2 sentence assessment with evidence>"
    }
  ],
  "overall_risk_score": <float 0.0–10.0>,
  "recommendation": "<approve|approve_with_conditions|reject>",
  "summary": "<2–4 sentence overall financial risk assessment>",
  "conditions": ["<condition if approve_with_conditions, else empty list>"]
}

Risk / recommendation guidance:
- overall_risk_score 0–3   → LOW    → approve
- overall_risk_score 3–6   → MEDIUM → approve_with_conditions
- overall_risk_score 6–8   → HIGH   → approve_with_conditions or reject
- overall_risk_score 8–10  → CRITICAL → reject

For each domain, produce 1–3 findings. If information is unavailable, note it with risk_level MEDIUM and value 'Not disclosed'.
Be specific. Quote financial figures from vendor documents wherever possible."""

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

_RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


@dataclasses.dataclass
class FinancialFinding:
    category: str
    value: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    notes: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class FinancialAnalysisResult:
    findings: list[FinancialFinding]
    overall_risk_score: float
    recommendation: Literal["approve", "approve_with_conditions", "reject"]
    summary: str
    conditions: list[str]

    def to_dict(self) -> dict:
        return {
            "findings": [f.to_dict() for f in self.findings],
            "overall_risk_score": self.overall_risk_score,
            "recommendation": self.recommendation,
            "summary": self.summary,
            "conditions": self.conditions,
        }


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class FinancialAnalyzer:
    """
    Retrieves financial risk frameworks from kb_financial, fetches relevant
    vendor document sections, and produces a financial risk assessment with
    per-domain findings and an overall risk score.
    """

    def __init__(self, llm: LLMClient, retriever: Retriever):
        self.llm = llm
        self.retriever = retriever

    async def analyze(self, vendor_id: int, doc_id: int) -> FinancialAnalysisResult:
        """
        Run domain-scoped RAG+LLM calls and aggregate into a FinancialAnalysisResult.
        JSONDecodeError propagates to WorkflowService which sets ReviewStatus.ERROR.
        """
        vendor_collection = f"vendor_{vendor_id}_FINANCIAL_{doc_id}"

        all_findings: list[FinancialFinding] = []
        domain_results: list[dict] = []

        for domain, query in FINANCIAL_RETRIEVAL_QUERIES.items():
            try:
                kb_context = self.retriever.retrieve(query, "kb_financial", n=3)
            except Exception:
                kb_context = ""

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
                f"## Financial assessment domain: {domain.replace('_', ' ').title()}\n\n"
                f"### Financial risk framework excerpts\n"
                + (kb_context if kb_context else "(No framework excerpts available)")
                + f"\n\n### Vendor document excerpts\n"
                + (vendor_context if vendor_context else "(No vendor document excerpts available)")
                + "\n\nAssess the vendor's financial risk for this domain and return the JSON object."
            )

            raw_dict = await self.llm.complete_with_json_output(_SYSTEM_PROMPT, user_prompt)
            domain_results.append(raw_dict)

            for finding_dict in raw_dict.get("findings", []):
                all_findings.append(
                    FinancialFinding(
                        category=finding_dict.get("category", "Unknown"),
                        value=finding_dict.get("value", "Not disclosed"),
                        risk_level=finding_dict.get("risk_level", "MEDIUM"),
                        notes=finding_dict.get("notes", ""),
                    )
                )

        # Aggregate: mean risk score, worst-case recommendation
        scores = [r.get("overall_risk_score", 5.0) for r in domain_results]
        overall_risk_score = round(sum(scores) / len(scores), 1) if scores else 5.0

        _REC_ORDER = {"approve": 0, "approve_with_conditions": 1, "reject": 2}
        recommendation = "approve"
        summary = ""
        all_conditions: list[str] = []

        for result in domain_results:
            rec = result.get("recommendation", "approve")
            if _REC_ORDER.get(rec, 0) > _REC_ORDER.get(recommendation, 0):
                recommendation = rec
            if result.get("summary"):
                summary = result["summary"]
            all_conditions.extend(result.get("conditions", []))

        if not summary and domain_results:
            summary = domain_results[-1].get("summary", "")

        seen: set[str] = set()
        deduped_conditions: list[str] = []
        for c in all_conditions:
            if c not in seen:
                seen.add(c)
                deduped_conditions.append(c)

        return FinancialAnalysisResult(
            findings=all_findings,
            overall_risk_score=overall_risk_score,
            recommendation=recommendation,  # type: ignore[arg-type]
            summary=summary,
            conditions=deduped_conditions,
        )

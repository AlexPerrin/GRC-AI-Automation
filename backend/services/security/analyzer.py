"""
SecurityAnalyzer — Stage 3 RAG-powered security risk evaluation module.
Fully implemented in Day 4.
"""
from __future__ import annotations

import dataclasses
import logging
from typing import Literal

from services.llm.client import LLMClient
from services.rag.retriever import Retriever

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retrieval queries — one per control domain
# ---------------------------------------------------------------------------

SECURITY_RETRIEVAL_QUERIES: dict[str, str] = {
    "access_control": "MFA multi-factor authentication least privilege access management",
    "data_protection": "encryption at rest in transit key management data security",
    "incident_response": "incident response breach notification SLA detection",
    "vulnerability_management": "penetration testing patching vulnerability scanning CVE",
    "business_continuity": "disaster recovery RTO RPO backup business continuity",
    "supply_chain": "third party vendor assessment software composition supply chain",
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a senior information security analyst performing a vendor security risk assessment.

You will be given:
1. Security control requirements retrieved from the knowledge base (NIST CSF, SOC 2, ISO 27001).
2. Excerpts from the vendor's security documentation.

You MUST output a single JSON object — no markdown fences, no commentary — with exactly this schema:

{
  "control_findings": [
    {
      "domain": "<control domain, e.g. access_control>",
      "framework": "<e.g. NIST CSF>",
      "control_id": "<e.g. PR.AC>",
      "status": "<met|partial|not_met|not_applicable>",
      "finding": "<1-3 sentence assessment>",
      "evidence": "<quoted text from vendor document OR 'No evidence found'>",
      "risk_score": <integer 1-5>
    }
  ],
  "overall_risk": "<low|medium|high|critical>",
  "recommendation": "<approve|approve_with_conditions|reject>",
  "summary": "<2-4 sentence overall assessment>",
  "conditions": ["<remediation condition if approve_with_conditions, else empty list>"]
}

Risk score guidance (per finding):
  1 = control fully met, no gaps
  2 = minor gaps, low risk
  3 = significant gaps, medium risk
  4 = major deficiencies, high risk
  5 = control absent or critically deficient

Overall risk / recommendation guidance:
  avg score <= 2.0  -> low    -> approve
  avg score <= 3.0  -> medium -> approve_with_conditions
  avg score <= 4.0  -> high   -> approve_with_conditions or reject
  avg score > 4.0   -> critical -> reject

Be specific. Reference control IDs and cite vendor text wherever possible."""

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
_RECOMMENDATION_ORDER = {"approve": 0, "approve_with_conditions": 1, "reject": 2}


@dataclasses.dataclass
class ControlFinding:
    domain: str
    framework: str
    control_id: str
    status: Literal["met", "partial", "not_met", "not_applicable"]
    finding: str
    evidence: str
    risk_score: int  # 1-5

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class SecurityAnalysisResult:
    control_findings: list[ControlFinding]
    overall_risk: Literal["low", "medium", "high", "critical"]
    recommendation: Literal["approve", "approve_with_conditions", "reject"]
    summary: str
    conditions: list[str]
    risk_score: float  # mean risk_score across all findings

    def to_dict(self) -> dict:
        return {
            "control_findings": [f.to_dict() for f in self.control_findings],
            "overall_risk": self.overall_risk,
            "recommendation": self.recommendation,
            "summary": self.summary,
            "conditions": self.conditions,
            "risk_score": self.risk_score,
        }


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class SecurityAnalyzer:
    """
    Retrieves control requirements from kb_security and relevant sections
    from the vendor's security documentation, then produces a domain-level
    risk report with scores, gap descriptions, and a risk disposition.

    The NDA gate (vendor must be in SECURITY_REVIEW status) is enforced by
    WorkflowService before calling analyze().
    """

    def __init__(self, llm: LLMClient, retriever: Retriever):
        self.llm = llm
        self.retriever = retriever

    async def analyze(self, vendor_id: int, doc_id: int) -> SecurityAnalysisResult:
        """
        Run 6 domain-scoped RAG+LLM calls and aggregate into a single
        SecurityAnalysisResult.

        JSONDecodeError from complete_with_json_output is intentionally NOT
        caught here — it propagates to WorkflowService which sets ReviewStatus.ERROR.
        """
        vendor_collection = f"vendor_{vendor_id}_SECURITY_{doc_id}"

        all_findings: list[ControlFinding] = []
        domain_results: list[dict] = []

        for domain, query in SECURITY_RETRIEVAL_QUERIES.items():
            kb_context = self.retriever.retrieve(query, "kb_security", n=3)

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
                f"## Security control domain: {domain.replace('_', ' ').title()}\n\n"
                f"### Control requirements (knowledge base)\n{kb_context}\n\n"
                f"### Vendor security documentation excerpts\n"
                + (vendor_context if vendor_context else "(No vendor documentation excerpts available)")
                + "\n\nAssess the vendor's controls for this domain and return the JSON object."
            )

            raw_dict = await self.llm.complete_with_json_output(_SYSTEM_PROMPT, user_prompt)
            domain_results.append(raw_dict)

            for finding_dict in raw_dict.get("control_findings", []):
                all_findings.append(
                    ControlFinding(
                        domain=finding_dict.get("domain", domain),
                        framework=finding_dict.get("framework", ""),
                        control_id=finding_dict.get("control_id", ""),
                        status=finding_dict.get("status", "not_applicable"),
                        finding=finding_dict.get("finding", ""),
                        evidence=finding_dict.get("evidence", "No evidence found"),
                        risk_score=int(finding_dict.get("risk_score", 3)),
                    )
                )

        # Aggregate: worst-case risk + recommendation; mean risk score
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

        if not summary and domain_results:
            summary = domain_results[-1].get("summary", "")

        # Deduplicate conditions preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for c in all_conditions:
            if c not in seen:
                seen.add(c)
                deduped.append(c)

        mean_score = (
            round(sum(f.risk_score for f in all_findings) / len(all_findings), 2)
            if all_findings
            else 0.0
        )

        return SecurityAnalysisResult(
            control_findings=all_findings,
            overall_risk=overall_risk,  # type: ignore[arg-type]
            recommendation=recommendation,  # type: ignore[arg-type]
            summary=summary,
            conditions=deduped,
            risk_score=mean_score,
        )

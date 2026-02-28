"""
Demo: End-to-end Security AI Analysis
======================================
Runs a real SecurityAnalyzer.analyze() call against a sample vendor
information security policy document.

Steps:
  1. Seeds kb_security (NIST CSF, SOC 2, ISO 27001) into ChromaDB if absent
  2. Chunks and embeds a realistic-but-intentionally-incomplete security policy
     into a vendor-specific collection
  3. Calls SecurityAnalyzer.analyze() — 6 RAG+LLM calls, one per control domain
  4. Pretty-prints the structured SecurityAnalysisResult

Intentional gaps in the sample document:
  ✓  MFA for privileged accounts, RBAC, AES-256 + TLS
  ✓  Annual penetration testing, SOC 2 Type II
  ✗  No incident response SLA or breach notification timeline
  ✗  No formal vulnerability management / patching cadence
  ✗  No defined RTO / RPO or tested DR plan
  ✗  No third-party / supply chain security assessment process
  ✗  MFA not enforced for all remote access (only admins)

Run from the backend directory:
  .venv/bin/python demo_security_analysis.py
"""
import asyncio
import json
import os
import textwrap
from pathlib import Path

# ── Load .env ─────────────────────────────────────────────────────────────────
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

_chroma_dir = Path(__file__).parent / "chroma_demo"
_chroma_dir.mkdir(exist_ok=True)
os.environ["CHROMA_PERSIST_DIR"] = str(_chroma_dir)
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import logging
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

# ── Sample vendor security policy ─────────────────────────────────────────────
SAMPLE_SECURITY_POLICY = """
CLOUDPAY SOLUTIONS — INFORMATION SECURITY POLICY
Document ID: ISP-001  |  Version: 1.8  |  Owner: CISO
Effective Date: 1 March 2025  |  Review Cycle: Annual

1. SCOPE AND PURPOSE
This policy governs the information security programme at CloudPay Solutions Ltd
("CloudPay"), a cloud-based payroll and HR platform processing sensitive employee
and financial data for enterprise customers.  It applies to all staff, contractors,
and systems that access, store, or process CloudPay data.

2. ACCESS CONTROL
2.1  Identity and Access Management
  All CloudPay systems enforce role-based access control (RBAC).  Access rights are
  assigned based on the principle of least privilege and reviewed quarterly by team
  leads.  Privileged (admin) accounts require multi-factor authentication (MFA) using
  TOTP or hardware security keys.  Standard employee accounts use username and password;
  MFA for non-privileged remote access is planned for Q3 2025.

2.2  Onboarding and Offboarding
  Access is provisioned within 24 hours of HR approval.  Upon termination, access is
  revoked within 4 business hours.  Shared credentials are prohibited; all accounts
  are individually attributed.

2.3  Privileged Access
  Privileged access sessions are logged and retained for 12 months.  Production
  environment access requires a formal change request approved by the Engineering
  Manager.

3. DATA PROTECTION
3.1  Encryption
  All data at rest is encrypted using AES-256.  All data in transit is protected with
  TLS 1.2 or higher.  Database backups are encrypted using the same standard.

3.2  Data Classification
  CloudPay classifies data into four tiers: Public, Internal, Confidential, and
  Restricted.  Payroll and personal data is classified as Restricted and subject to
  the most stringent access and handling controls.

3.3  Key Management
  Encryption keys are managed via AWS Key Management Service (KMS).  Key rotation
  is performed annually for symmetric keys.  Key access is restricted to authorised
  services and audited monthly.

4. SECURITY TESTING
4.1  Penetration Testing
  CloudPay engages an independent third-party firm to conduct an annual penetration
  test of the production environment.  The most recent test was completed in
  October 2024; no critical findings were identified.  High-severity findings are
  remediated within 30 days.

4.2  Vulnerability Scanning
  Automated vulnerability scans are run on web-facing assets on an ad-hoc basis
  following deployments.  There is no scheduled recurring scan cadence.  Internal
  network scanning is not currently performed.  A formal vulnerability management
  programme is under development.

5. INCIDENT RESPONSE
5.1  Incident Classification
  Security incidents are classified as Low, Medium, High, or Critical based on
  potential impact.  All suspected incidents must be reported to the Security team
  via the internal ticketing system.

5.2  Response Process
  Upon classification, the Security team coordinates investigation and containment.
  Post-incident reviews are conducted for High and Critical events.  There is no
  documented SLA for initial response or resolution times.  Customer notification
  procedures for data breaches are under review.

6. BUSINESS CONTINUITY
6.1  Backups
  All production databases are backed up daily with a 30-day retention period.
  Backup integrity is verified monthly via automated checksums.

6.2  Recovery Capability
  CloudPay infrastructure is hosted across two AWS availability zones to provide
  redundancy.  Formal disaster recovery (DR) runbooks are in draft.  No RTO or RPO
  targets have been formally defined or tested.  A tabletop DR exercise is planned
  for H2 2025.

7. THIRD-PARTY AND SUPPLY CHAIN SECURITY
7.1  Vendor Assessment
  CloudPay relies on third-party cloud services including AWS (infrastructure),
  Datadog (monitoring), and Stripe (payment processing).  Vendors are selected based
  on commercial and functional criteria.  Formal security assessments of third-party
  providers are not currently conducted.  All major cloud vendors maintain their own
  compliance certifications (SOC 2, ISO 27001) which CloudPay reviews during
  procurement.

7.2  Software Dependencies
  Application dependencies are managed via standard package managers.  No formal
  software composition analysis (SCA) or open-source licence scanning is in place.

8. COMPLIANCE
  CloudPay maintains SOC 2 Type II certification covering the Security and
  Availability trust service criteria.  The most recent audit report was issued
  in September 2024 with no exceptions.  ISO 27001 certification is targeted
  for 2026.
"""

# ── Formatting helpers ─────────────────────────────────────────────────────────
DIVIDER = "─" * 72

STATUS_EMOJI = {
    "met":            "✅",
    "partial":        "⚠️ ",
    "not_met":        "❌",
    "not_applicable": "➖",
}
RISK_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
REC_EMOJI = {
    "approve":                 "✅",
    "approve_with_conditions": "⚠️ ",
    "reject":                  "❌",
}

def wrap(text: str, width: int = 68, indent: str = "    ") -> str:
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


# ── Main ───────────────────────────────────────────────────────────────────────
async def main():
    print(f"\n{DIVIDER}")
    print("  GRC AI Automation — Security Analysis Demo")
    print("  Vendor: CloudPay Solutions Ltd")
    print(f"{DIVIDER}\n")

    # Step 1: Seed kb_security
    from services.knowledge_base.loader import KnowledgeBaseLoader
    from services.rag.store import VectorStore

    store = VectorStore()
    loader = KnowledgeBaseLoader(store=store)

    print("[ 1/3 ]  Seeding security controls knowledge base (kb_security) …")
    await loader.seed_if_empty()
    print("         Done.\n")

    # Step 2: Chunk & embed security policy
    from services.document.chunker import DocumentChunker

    vendor_id  = 1
    doc_id     = 2          # distinct from the legal demo's doc_id=1
    collection = f"vendor_{vendor_id}_SECURITY_{doc_id}"

    print(f"[ 2/3 ]  Embedding vendor security policy → collection '{collection}' …")
    chunker = DocumentChunker()
    chunks  = chunker.chunk(
        SAMPLE_SECURITY_POLICY,
        {"vendor": "CloudPay Solutions", "doc": "information_security_policy"},
    )
    store.upsert_chunks(collection, chunks)
    print(f"         {len(chunks)} chunks embedded.\n")

    # Step 3: Run Security AI Analysis
    from services.llm.client import LLMClient
    from services.rag.retriever import Retriever
    from services.security.analyzer import SecurityAnalyzer

    print("[ 3/3 ]  Running Security AI Analysis (6 domain calls) …")
    print(f"         Model  : {os.environ.get('LLM_PROVIDER', '?')}/{os.environ.get('LLM_MODEL', '?')}")
    print()

    analyzer = SecurityAnalyzer(
        llm=LLMClient(),
        retriever=Retriever(store=store),
    )
    result = await analyzer.analyze(vendor_id=vendor_id, doc_id=doc_id)

    # ── Print results ──────────────────────────────────────────────────────────
    risk_icon = RISK_EMOJI.get(result.overall_risk, "?")
    rec_icon  = REC_EMOJI.get(result.recommendation, "?")

    print(f"{DIVIDER}")
    print(f"  SECURITY ANALYSIS RESULT")
    print(f"{DIVIDER}")
    print(f"  Overall Risk    : {risk_icon}  {result.overall_risk.upper()}")
    print(f"  Mean Risk Score : {result.risk_score:.1f} / 5.0")
    print(f"  Recommendation  : {rec_icon}  {result.recommendation.replace('_', ' ').upper()}")
    print()
    print("  Summary:")
    print(wrap(result.summary))
    print()

    if result.conditions:
        print(f"  Conditions ({len(result.conditions)}):")
        for i, c in enumerate(result.conditions, 1):
            print(wrap(f"{i}. {c}"))
        print()

    print(f"{DIVIDER}")
    print(f"  CONTROL FINDINGS  ({len(result.control_findings)} total)")
    print(f"{DIVIDER}")

    for f in result.control_findings:
        icon = STATUS_EMOJI.get(f.status, "?")
        score_bar = "█" * f.risk_score + "░" * (5 - f.risk_score)
        print(f"\n  {icon}  [{f.framework}]  {f.control_id}  —  {f.domain.replace('_', ' ').title()}"
              f"  [risk {f.risk_score}/5  {score_bar}]  [{f.status.upper()}]")
        print(wrap(f.finding))
        if f.evidence and f.evidence != "No evidence found":
            print(f"     Evidence: \"{f.evidence[:120]}{'…' if len(f.evidence) > 120 else ''}\"")
        else:
            print("     Evidence: No evidence found")

    print(f"\n{DIVIDER}")
    print("  Raw JSON output")
    print(f"{DIVIDER}\n")
    print(json.dumps(result.to_dict(), indent=2))
    print()


if __name__ == "__main__":
    asyncio.run(main())

"""
Demo: End-to-end Legal AI Analysis
===================================
Runs a real LegalAnalyzer.analyze() call against a sample vendor privacy policy.

Steps:
  1. Seeds kb_legal (GDPR, PIPEDA, CPPA, HIPAA, PCI DSS) into ChromaDB if absent
  2. Chunks and embeds a realistic-but-intentionally-incomplete privacy policy
     into a vendor-specific collection
  3. Calls LegalAnalyzer.analyze() — 6 RAG+LLM calls, one per compliance domain
  4. Pretty-prints the structured LegalAnalysisResult

Run from the backend directory:
  .venv/bin/python demo_legal_analysis.py
"""
import asyncio
import json
import os
import sys
import textwrap

# Load .env from repo root
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# Use a writable Chroma directory (the default may be owned by root in dev)
_chroma_dir = Path(__file__).parent / "chroma_demo"
_chroma_dir.mkdir(exist_ok=True)
os.environ["CHROMA_PERSIST_DIR"] = str(_chroma_dir)

# Suppress ChromaDB's broken telemetry client (posthog signature mismatch)
os.environ["ANONYMIZED_TELEMETRY"] = "False"
import logging
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

# ── Sample vendor privacy policy ─────────────────────────────────────────────
# Intentionally incomplete:
#   ✓  Has some GDPR language, lawful basis mention, encryption claim
#   ✗  No explicit data subject rights process / request mechanism
#   ✗  No DPA / Art. 28 sub-processor clause
#   ✗  No mention of international transfer safeguards (SCCs / adequacy)
#   ✗  Vague retention period ("reasonable time")
#   ✗  No breach notification timeline

SAMPLE_PRIVACY_POLICY = """
CLOUDPAY SOLUTIONS — PRIVACY POLICY
Effective Date: 1 January 2025
Version: 2.3

1. INTRODUCTION
CloudPay Solutions Ltd ("CloudPay", "we", "us") provides cloud-based payroll
processing and HR management services to enterprise customers globally.  This
Privacy Policy describes how we collect, use, store, and protect personal data
belonging to our customers' employees and end-users ("Data Subjects").

2. DATA WE COLLECT
We collect the following categories of personal data:
  - Identity data: full legal name, date of birth, national insurance / tax ID
  - Contact data: work email address, telephone number, home address
  - Financial data: bank account details, salary information, payroll history
  - Employment data: job title, department, employment contract terms
  - Usage data: login timestamps, IP addresses, browser type

3. LAWFUL BASIS FOR PROCESSING (GDPR Art. 6)
We process personal data on the following lawful bases:
  - Contractual necessity: payroll processing requires handling financial and
    identity data to fulfil our obligations to client organisations.
  - Legal obligation: we retain tax records as required by applicable law.
  - Legitimate interests: fraud prevention and platform security monitoring.

We do not rely on consent as a primary lawful basis for payroll processing.

4. DATA SECURITY
CloudPay employs industry-standard security measures including:
  - AES-256 encryption for data at rest
  - TLS 1.2 or higher for all data in transit
  - Role-based access controls limiting staff access to personal data
  - Regular third-party penetration testing (annually)
  - SOC 2 Type II certified infrastructure

We maintain an information security policy reviewed annually by our CISO.

5. DATA RETENTION
We retain personal data for as long as reasonably necessary to fulfil the
purposes outlined in this policy, or as required by applicable law.  Upon
contract termination, client data is deleted within 90 days unless a longer
retention period is legally mandated.

6. THIRD-PARTY SERVICE PROVIDERS
CloudPay engages third-party vendors to support service delivery, including
cloud infrastructure providers and analytics platforms.  We require all vendors
to protect personal data in accordance with applicable law.  A list of current
sub-processors is available on request.

7. CONTACT US
For privacy-related enquiries, contact our Data Protection Officer:
  dpo@cloudpay.example.com
  CloudPay Solutions Ltd, 12 Finance Street, London, EC2V 8RT, United Kingdom

8. CHANGES TO THIS POLICY
We may update this policy from time to time.  Material changes will be
communicated to client organisations at least 30 days in advance.
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

DIVIDER = "─" * 72
STATUS_EMOJI = {
    "compliant":       "✅",
    "partial":         "⚠️ ",
    "non_compliant":   "❌",
    "not_applicable":  "➖",
}
RISK_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
REC_EMOJI = {
    "approve":                  "✅",
    "approve_with_conditions":  "⚠️ ",
    "reject":                   "❌",
}

def wrap(text: str, width: int = 68, indent: str = "    ") -> str:
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


async def main():
    print(f"\n{DIVIDER}")
    print("  GRC AI Automation — Legal Analysis Demo")
    print(f"  Vendor: CloudPay Solutions Ltd")
    print(f"{DIVIDER}\n")

    # ── Step 1: Seed knowledge base ──────────────────────────────────────────
    from services.knowledge_base.loader import KnowledgeBaseLoader
    from services.rag.store import VectorStore

    store = VectorStore()
    loader = KnowledgeBaseLoader(store=store)

    print("[ 1/3 ]  Seeding regulatory knowledge base (kb_legal) …")
    await loader.seed_if_empty()
    print("         Done.\n")

    # ── Step 2: Chunk & embed sample privacy policy ──────────────────────────
    from services.document.chunker import DocumentChunker

    vendor_id = 1
    doc_id    = 1
    collection = f"vendor_{vendor_id}_LEGAL_{doc_id}"

    print(f"[ 2/3 ]  Embedding vendor privacy policy → collection '{collection}' …")
    chunker = DocumentChunker()
    chunks  = chunker.chunk(SAMPLE_PRIVACY_POLICY, {"vendor": "CloudPay Solutions", "doc": "privacy_policy"})
    store.upsert_chunks(collection, chunks)
    print(f"         {len(chunks)} chunks embedded.\n")

    # ── Step 3: Run Legal AI Analysis ────────────────────────────────────────
    from services.legal.analyzer import LegalAnalyzer
    from services.llm.client import LLMClient
    from services.rag.retriever import Retriever

    print("[ 3/3 ]  Running Legal AI Analysis (6 domain calls) …")
    print(f"         Model  : {os.environ.get('LLM_PROVIDER', '?')}/{os.environ.get('LLM_MODEL', '?')}")
    print()

    analyzer = LegalAnalyzer(
        llm=LLMClient(),
        retriever=Retriever(store=store),
    )
    result = await analyzer.analyze(vendor_id=vendor_id, doc_id=doc_id)

    # ── Print results ─────────────────────────────────────────────────────────
    risk_icon = RISK_EMOJI.get(result.overall_risk, "?")
    rec_icon  = REC_EMOJI.get(result.recommendation, "?")

    print(f"{DIVIDER}")
    print(f"  LEGAL ANALYSIS RESULT")
    print(f"{DIVIDER}")
    print(f"  Overall Risk    : {risk_icon}  {result.overall_risk.upper()}")
    print(f"  Recommendation  : {rec_icon}  {result.recommendation.replace('_', ' ').upper()}")
    print()
    print(f"  Summary:")
    print(wrap(result.summary))
    print()

    if result.conditions:
        print(f"  Conditions ({len(result.conditions)}):")
        for i, c in enumerate(result.conditions, 1):
            print(wrap(f"{i}. {c}"))
        print()

    print(f"{DIVIDER}")
    print(f"  REGULATION FINDINGS  ({len(result.regulation_findings)} total)")
    print(f"{DIVIDER}")

    for f in result.regulation_findings:
        icon = STATUS_EMOJI.get(f.status, "?")
        print(f"\n  {icon}  {f.regulation}  {f.article}  [{f.status.upper()}]")
        print(wrap(f.finding))
        if f.evidence and f.evidence != "No evidence found":
            print(f"     Evidence: \"{f.evidence[:120]}{'…' if len(f.evidence) > 120 else ''}\"")
        else:
            print(f"     Evidence: No evidence found")

    print(f"\n{DIVIDER}")
    print(f"  Raw JSON output (saved below)")
    print(f"{DIVIDER}\n")
    print(json.dumps(result.to_dict(), indent=2))
    print()


if __name__ == "__main__":
    asyncio.run(main())

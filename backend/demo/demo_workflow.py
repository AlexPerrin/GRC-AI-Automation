"""
Demo: End-to-End Vendor Onboarding Workflow
============================================
Walks a vendor through all four stages without requiring an LLM API key.
AI review stages (Legal, Security) are seeded directly so the demo focuses
on the workflow orchestration implemented in Day 5.

Run from the backend directory:
  .venv/bin/python demo_workflow.py
"""
import os
import sys

# In-memory DB — must be set before any app import
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("LLM_PROVIDER_API_KEY", "demo-key")
os.environ.setdefault("CHROMA_HOST", "")

from datetime import datetime
from pathlib import Path
from textwrap import indent
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from core.models import DocumentStage, Review, ReviewStatus, ReviewType, Vendor, VendorStatus
from main import app, KnowledgeBaseLoader

# ── setup ──────────────────────────────────────────────────────────────────

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

db = Session()

def override_get_db():
    yield db

app.dependency_overrides[get_db] = override_get_db

# ── helpers ────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
DIM    = "\033[2m"

WIDTH = 66

def banner(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'━' * WIDTH}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'━' * WIDTH}{RESET}")

def step(label: str, status_before: str, status_after: str, detail: str = "") -> None:
    arrow = f"{YELLOW}➜{RESET}"
    ok    = f"{GREEN}✓{RESET}"
    print(f"\n  {ok} {BOLD}{label}{RESET}")
    print(f"     {DIM}{status_before}{RESET}  {arrow}  {GREEN}{status_after}{RESET}")
    if detail:
        for line in detail.splitlines():
            print(f"     {DIM}{line}{RESET}")

def show_json(label: str, data: dict) -> None:
    import json
    print(f"  {DIM}{label}:{RESET}")
    lines = json.dumps(data, indent=4, default=str).splitlines()
    for line in lines[:20]:
        print(f"  {DIM}{line}{RESET}")
    if len(lines) > 20:
        print(f"  {DIM}  ... ({len(lines) - 20} more lines){RESET}")

def seed_ai_review(vendor_id: int, stage: DocumentStage, ai_output: dict) -> Review:
    """Insert a pre-completed AI review row directly — skips real LLM call."""
    review = Review(
        vendor_id=vendor_id,
        stage=stage,
        review_type=ReviewType.AI_ANALYSIS,
        status=ReviewStatus.COMPLETE,
        ai_output=ai_output,
        completed_at=datetime.utcnow(),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

# ── demo ───────────────────────────────────────────────────────────────────

with patch.object(KnowledgeBaseLoader, "seed_if_empty", new_callable=AsyncMock):
    with TestClient(app) as client:

        banner("Day 5 Workflow Demo  —  Vendor Onboarding Pipeline")
        print(f"\n  {DIM}Four stages: Use Case → Legal → Security → Financial{RESET}")
        print(f"  {DIM}Human-form stages fully wired; AI stages seeded with mock output{RESET}")

        # ── Stage 0: Create vendor ──────────────────────────────────────
        banner("Stage 0 — Create Vendor")

        resp = client.post("/vendors/", json={
            "name": "Acme Analytics Ltd",
            "website": "https://acme-analytics.example.com",
            "description": "Cloud-based data analytics platform",
        })
        assert resp.status_code == 201, resp.text
        vendor = resp.json()
        step("Vendor created", "—", vendor["status"],
             f"id={vendor['id']}  name={vendor['name']}")

        vendor_id = vendor["id"]

        # ── Stage 1: Use Case (human form) ─────────────────────────────
        banner("Stage 1 — Use Case Evaluation  (human form)")

        resp = client.post(f"/vendors/{vendor_id}/start-intake")
        assert resp.status_code == 200, resp.text
        step("Intake started", "INTAKE", resp.json()["status"])

        resp = client.get(f"/vendors/{vendor_id}/reviews")
        use_case_review = resp.json()[0]

        resp = client.post(f"/reviews/{use_case_review['id']}/submit-form", json={
            "use_case_description": "Real-time analytics dashboards for ops team",
            "business_justification": "Reduce reporting lag from 3 days to real-time",
            "data_types_involved": ["aggregated_metrics", "usage_logs"],
            "estimated_users": 120,
            "alternatives_considered": "In-house Tableau — too expensive to scale",
            "reviewer_name": "Sarah Chen",
            "recommendation": "PROCEED",
            "notes": "Low data sensitivity. No PII involved.",
        })
        assert resp.status_code == 200, resp.text
        step(
            "Use case form submitted — PROCEED",
            "USE_CASE_REVIEW",
            client.get(f"/vendors/{vendor_id}").json()["status"],
            "reviewer: Sarah Chen",
        )

        # ── Stage 2: Legal (AI analysis + human decision) ───────────────
        banner("Stage 2 — Legal / Regulatory Review  (AI + human decision)")

        legal_ai_output = {
            "overall_risk": "LOW",
            "recommendation": "APPROVE",
            "domains": {
                "GDPR": {"risk": "LOW", "findings": ["DPA clause present", "Right-to-erasure documented"]},
                "PIPEDA": {"risk": "LOW", "findings": ["Consent mechanisms documented"]},
                "HIPAA": {"risk": "N/A", "findings": ["No PHI involved"]},
            },
            "summary": "Vendor demonstrates adequate legal and regulatory compliance.",
        }
        legal_review = seed_ai_review(vendor_id, DocumentStage.LEGAL, legal_ai_output)

        # Manually advance vendor to LEGAL_REVIEW for the decision guard
        v = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        v.status = VendorStatus.LEGAL_REVIEW
        db.commit()

        step("AI legal analysis complete (seeded)", "USE_CASE_APPROVED", "LEGAL_REVIEW",
             "overall_risk=LOW  recommendation=APPROVE")
        show_json("AI output", legal_ai_output)

        resp = client.post(f"/reviews/{legal_review.id}/decisions", json={
            "actor": "legal_team",
            "action": "APPROVE",
            "rationale": "Adequate GDPR and PIPEDA compliance. No HIPAA exposure.",
            "conditions": [],
        })
        assert resp.status_code == 201, resp.text
        step(
            "Legal decision recorded — APPROVE",
            "LEGAL_REVIEW",
            client.get(f"/vendors/{vendor_id}").json()["status"],
            "actor: legal_team",
        )

        # ── NDA Gate ───────────────────────────────────────────────────
        banner("NDA Gate")

        resp = client.post(f"/vendors/{vendor_id}/confirm-nda")
        assert resp.status_code == 200, resp.text
        step("NDA confirmed", "LEGAL_APPROVED", resp.json()["status"])

        # ── Stage 3: Security (AI analysis + human decision) ────────────
        banner("Stage 3 — Security Risk Evaluation  (AI + human decision)")

        security_ai_output = {
            "overall_risk": "MEDIUM",
            "risk_score": 42,
            "recommendation": "APPROVE_WITH_CONDITIONS",
            "categories": {
                "data_encryption": {"risk": "LOW",    "findings": ["AES-256 at rest", "TLS 1.3 in transit"]},
                "access_controls": {"risk": "MEDIUM", "findings": ["MFA optional, not enforced for all users"]},
                "incident_response": {"risk": "LOW",  "findings": ["IR plan documented, tested annually"]},
                "vendor_supply_chain": {"risk": "LOW", "findings": ["SOC 2 Type II current"]},
            },
            "summary": "Acceptable risk profile with one remediation required before go-live.",
        }
        security_review = seed_ai_review(vendor_id, DocumentStage.SECURITY, security_ai_output)

        step("AI security analysis complete (seeded)", "SECURITY_REVIEW", "SECURITY_REVIEW",
             "overall_risk=MEDIUM  risk_score=42  recommendation=APPROVE_WITH_CONDITIONS")
        show_json("AI output", security_ai_output)

        resp = client.post(f"/reviews/{security_review.id}/decisions", json={
            "actor": "security_team",
            "action": "APPROVE_WITH_CONDITIONS",
            "rationale": "Acceptable risk. MFA enforcement required before production access.",
            "conditions": ["Enforce MFA for all admin accounts within 30 days"],
        })
        assert resp.status_code == 201, resp.text
        step(
            "Security decision recorded — APPROVE_WITH_CONDITIONS",
            "SECURITY_REVIEW",
            client.get(f"/vendors/{vendor_id}").json()["status"],
            "condition: Enforce MFA for all admin accounts within 30 days",
        )

        # ── Stage 4: Financial (human form) ────────────────────────────
        banner("Stage 4 — Financial Risk Evaluation  (human form)")

        resp = client.post(f"/vendors/{vendor_id}/start-financial-review")
        assert resp.status_code == 200, resp.text
        step("Financial review started", "SECURITY_APPROVED", resp.json()["status"])

        resp = client.get(f"/vendors/{vendor_id}/reviews")
        financial_review = next(r for r in resp.json() if r["stage"] == "FINANCIAL")

        resp = client.post(f"/reviews/{financial_review['id']}/submit-form", json={
            "vendor_annual_revenue": "$12M ARR",
            "years_in_operation": 7,
            "financial_documents_reviewed": ["audited_financials_2024", "SOC2_bridge_letter"],
            "concentration_risk_flag": False,
            "financial_stability_assessment": "STABLE",
            "contract_value": "$48,000/yr",
            "reviewer_name": "Marcus Webb",
            "recommendation": "ACCEPTABLE_WITH_CONDITIONS",
            "conditions": ["Escrow clause for SaaS continuity"],
            "notes": "Profitable, 7yr track record. Low concentration risk.",
        })
        assert resp.status_code == 200, resp.text
        step(
            "Financial form submitted — ACCEPTABLE_WITH_CONDITIONS",
            "FINANCIAL_REVIEW",
            client.get(f"/vendors/{vendor_id}").json()["status"],
            "reviewer: Marcus Webb  |  contract: $48,000/yr",
        )

        # ── Final: Complete Onboarding ──────────────────────────────────
        banner("Final — Complete Onboarding")

        resp = client.post(f"/vendors/{vendor_id}/complete-onboarding")
        assert resp.status_code == 200, resp.text
        final = resp.json()
        step("Onboarding complete!", "FINANCIAL_APPROVED", final["status"])

        # ── Audit Trail ────────────────────────────────────────────────
        banner("Audit Trail")

        from core.models import AuditLog
        logs = (
            db.query(AuditLog)
            .filter(AuditLog.vendor_id == vendor_id)
            .order_by(AuditLog.timestamp)
            .all()
        )
        print()
        for i, log in enumerate(logs, 1):
            ts = log.timestamp.strftime("%H:%M:%S") if log.timestamp else "?"
            print(f"  {DIM}{i:2}.{RESET}  {CYAN}{log.event_type:<35}{RESET}  "
                  f"{DIM}actor={log.actor}  ts={ts}{RESET}")

        # ── Summary ────────────────────────────────────────────────────
        banner("Summary")
        print(f"\n  {GREEN}{BOLD}✓ Vendor '{final['name']}' successfully onboarded{RESET}")
        print(f"  {DIM}id={final['id']}  final_status={final['status']}{RESET}")
        print(f"\n  {DIM}Stages completed:{RESET}")
        stages = [
            ("Stage 1", "Use Case Evaluation", "PROCEED",                      "Sarah Chen"),
            ("Stage 2", "Legal Review",         "APPROVE",                      "legal_team"),
            ("Gate",    "NDA Confirmed",         "—",                            "system"),
            ("Stage 3", "Security Review",       "APPROVE_WITH_CONDITIONS",     "security_team"),
            ("Stage 4", "Financial Review",      "ACCEPTABLE_WITH_CONDITIONS",  "Marcus Webb"),
        ]
        for tag, name, action, actor in stages:
            print(f"    {GREEN}✓{RESET}  {BOLD}{tag}{RESET}  {name:<30}  {DIM}{action}  ({actor}){RESET}")
        print()

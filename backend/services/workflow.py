"""
WorkflowService — orchestrates all four stage transitions and the audit log.
Stub for Day 1; fully implemented in Day 5.
"""
from sqlalchemy.orm import Session

from core.models import AuditLog, Vendor, VendorStatus
from schemas.forms import FinancialRiskFormInput, UseCaseFormInput


class WorkflowService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, vendor_id: int, event_type: str, actor: str, payload: dict) -> None:
        """Append an immutable entry to the audit log."""
        entry = AuditLog(
            vendor_id=vendor_id,
            event_type=event_type,
            actor=actor,
            payload=payload,
        )
        self.db.add(entry)
        # Caller is responsible for committing the transaction.

    # ------------------------------------------------------------------
    # Stage 1 — Use Case Evaluation (human form)
    # ------------------------------------------------------------------

    def create_vendor_and_intake(self, data) -> Vendor:
        """Create vendor record and open Stage 1 review. Implemented Day 5."""
        raise NotImplementedError

    def submit_use_case_form(self, review_id: int, form: UseCaseFormInput):
        """Validate and store Stage 1 form; advance workflow on PROCEED. Implemented Day 5."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Stage 2 — Legal / Regulatory Review (AI)
    # ------------------------------------------------------------------

    def trigger_legal_review(self, vendor_id: int, doc_id: int):
        """Kick off RAG-powered legal analysis. Implemented Day 3."""
        raise NotImplementedError

    def submit_legal_decision(self, review_id: int, action: str, rationale: str):
        """Record human decision on Stage 2 output. Implemented Day 5."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # NDA Gate
    # ------------------------------------------------------------------

    def confirm_nda(self, vendor_id: int) -> Vendor:
        """Advance LEGAL_APPROVED → SECURITY_REVIEW on NDA confirmation. Implemented Day 4."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Stage 3 — Security Risk Evaluation (AI)
    # ------------------------------------------------------------------

    def trigger_security_review(self, vendor_id: int, doc_id: int):
        """Kick off RAG-powered security analysis. Implemented Day 4."""
        raise NotImplementedError

    def submit_security_decision(self, review_id: int, action: str, rationale: str):
        """Record human decision on Stage 3 output. Implemented Day 5."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Stage 4 — Financial Risk Evaluation (human form)
    # ------------------------------------------------------------------

    def submit_financial_form(self, review_id: int, form: FinancialRiskFormInput):
        """Validate and store Stage 4 form; advance workflow on ACCEPTABLE. Implemented Day 5."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Final disposition
    # ------------------------------------------------------------------

    def complete_onboarding(self, vendor_id: int) -> Vendor:
        """Set vendor status to ONBOARDED after all stages approved. Implemented Day 5."""
        raise NotImplementedError

    def reject_vendor(self, vendor_id: int, stage: str, rationale: str) -> Vendor:
        """Reject vendor from any stage. Implemented Day 5."""
        raise NotImplementedError

"""
WorkflowService — orchestrates all four stage transitions and the audit log.
Stage 2 (trigger_legal_review) implemented in Day 3.
Stage 3 (confirm_nda, trigger_security_review) implemented in Day 4.
All other stages implemented in Day 5.
"""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from core.models import AuditLog, DocumentStage, Review, ReviewStatus, ReviewType, Vendor, VendorStatus
from schemas.forms import FinancialRiskFormInput, UseCaseFormInput
from services.legal.analyzer import LegalAnalyzer
from services.llm.client import LLMClient
from services.rag.retriever import Retriever
from services.rag.store import VectorStore
from services.security.analyzer import SecurityAnalyzer

logger = logging.getLogger(__name__)


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

    def create_vendor_and_intake(self, vendor_id: int) -> tuple:
        """Open Stage 1 review for an existing vendor in INTAKE status."""
        db = self.db

        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise ValueError(f"Vendor {vendor_id} not found")
        if vendor.status != VendorStatus.INTAKE:
            raise ValueError(
                f"Vendor must be in INTAKE status, current: {vendor.status}"
            )

        review = Review(
            vendor_id=vendor_id,
            stage=DocumentStage.USE_CASE,
            review_type=ReviewType.HUMAN_FORM,
            status=ReviewStatus.PENDING,
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        vendor.status = VendorStatus.USE_CASE_REVIEW
        db.commit()

        self._log(
            vendor_id=vendor_id,
            event_type="INTAKE_STARTED",
            actor="system",
            payload={"vendor_id": vendor_id, "review_id": review.id},
        )
        db.commit()

        db.refresh(vendor)
        return (vendor, review)

    def submit_use_case_form(self, review_id: int, form: UseCaseFormInput) -> Review:
        """Validate and store Stage 1 form; advance workflow on PROCEED."""
        db = self.db

        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")

        review.form_input = form.model_dump()
        review.status = ReviewStatus.COMPLETE
        review.completed_at = datetime.utcnow()
        db.commit()

        vendor = db.query(Vendor).filter(Vendor.id == review.vendor_id).first()
        if form.recommendation == "PROCEED":
            vendor.status = VendorStatus.USE_CASE_APPROVED
            self._log(
                vendor_id=review.vendor_id,
                event_type="USE_CASE_APPROVED",
                actor=form.reviewer_name,
                payload={"review_id": review_id},
            )
        else:
            vendor.status = VendorStatus.REJECTED
            self._log(
                vendor_id=review.vendor_id,
                event_type="VENDOR_REJECTED",
                actor=form.reviewer_name,
                payload={
                    "review_id": review_id,
                    "stage": "USE_CASE",
                    "rationale": form.notes,
                },
            )
        db.commit()

        db.refresh(review)
        return review

    # ------------------------------------------------------------------
    # Stage 2 — Legal / Regulatory Review (AI)
    # ------------------------------------------------------------------

    async def trigger_legal_review(self, review_id: int, doc_id: int) -> Review:
        """Kick off RAG-powered legal analysis and persist the result."""
        db = self.db

        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")

        review.status = ReviewStatus.IN_PROGRESS
        db.commit()

        vendor = db.query(Vendor).filter(Vendor.id == review.vendor_id).first()
        if vendor and vendor.status != VendorStatus.LEGAL_REVIEW:
            vendor.status = VendorStatus.LEGAL_REVIEW
            db.commit()

        analyzer = LegalAnalyzer(
            llm=LLMClient(),
            retriever=Retriever(store=VectorStore()),
        )

        try:
            result = await analyzer.analyze(review.vendor_id, doc_id)
            review.ai_output = result.to_dict()
            review.status = ReviewStatus.COMPLETE
            review.completed_at = datetime.utcnow()
            db.commit()

            self._log(
                vendor_id=review.vendor_id,
                event_type="LEGAL_REVIEW_COMPLETE",
                actor="system",
                payload={
                    "review_id": review_id,
                    "doc_id": doc_id,
                    "overall_risk": result.overall_risk,
                    "recommendation": result.recommendation,
                },
            )
            db.commit()

        except Exception as exc:
            logger.error(
                "Legal review failed for review_id=%s doc_id=%s: %s",
                review_id,
                doc_id,
                exc,
            )
            review.status = ReviewStatus.ERROR
            review.completed_at = datetime.utcnow()
            db.commit()

            self._log(
                vendor_id=review.vendor_id,
                event_type="LEGAL_REVIEW_ERROR",
                actor="system",
                payload={
                    "review_id": review_id,
                    "doc_id": doc_id,
                    "error": str(exc),
                },
            )
            db.commit()

        db.refresh(review)
        return review

    def submit_legal_decision(
        self,
        review_id: int,
        action: str,
        rationale: str,
        conditions: list | None = None,
        actor: str = "system",
    ) -> Vendor:
        """Record human decision on Stage 2 output; advance workflow state."""
        db = self.db

        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")
        if review.status != ReviewStatus.COMPLETE:
            raise ValueError("Review must be COMPLETE before a decision can be recorded")

        vendor = db.query(Vendor).filter(Vendor.id == review.vendor_id).first()
        if action in ("APPROVE", "APPROVE_WITH_CONDITIONS"):
            vendor.status = VendorStatus.LEGAL_APPROVED
            self._log(
                vendor_id=review.vendor_id,
                event_type="LEGAL_DECISION_APPROVED",
                actor=actor,
                payload={
                    "review_id": review_id,
                    "action": action,
                    "conditions": conditions or [],
                },
            )
        else:
            vendor.status = VendorStatus.REJECTED
            self._log(
                vendor_id=review.vendor_id,
                event_type="VENDOR_REJECTED",
                actor=actor,
                payload={
                    "review_id": review_id,
                    "stage": "LEGAL",
                    "action": action,
                    "rationale": rationale,
                },
            )
        db.commit()

        db.refresh(vendor)
        return vendor

    # ------------------------------------------------------------------
    # NDA Gate
    # ------------------------------------------------------------------

    def confirm_nda(self, vendor_id: int) -> Vendor:
        """
        Confirm NDA execution for a vendor.
        Requires vendor status == LEGAL_APPROVED; advances to SECURITY_REVIEW.
        Raises ValueError if the vendor is not found or in the wrong state.
        """
        db = self.db

        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise ValueError(f"Vendor {vendor_id} not found")
        if vendor.status != VendorStatus.LEGAL_APPROVED:
            raise ValueError(
                f"NDA confirmation requires status LEGAL_APPROVED, current: {vendor.status}"
            )

        vendor.status = VendorStatus.SECURITY_REVIEW
        db.commit()

        self._log(
            vendor_id=vendor_id,
            event_type="NDA_CONFIRMED",
            actor="system",
            payload={"vendor_id": vendor_id},
        )
        db.commit()

        db.refresh(vendor)
        return vendor

    # ------------------------------------------------------------------
    # Stage 3 — Security Risk Evaluation (AI)
    # ------------------------------------------------------------------

    async def trigger_security_review(self, review_id: int, doc_id: int) -> Review:
        """
        Kick off RAG-powered security analysis and persist the result.
        NDA gate: vendor must be in SECURITY_REVIEW status.
        """
        db = self.db

        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")

        vendor = db.query(Vendor).filter(Vendor.id == review.vendor_id).first()
        if not vendor or vendor.status != VendorStatus.SECURITY_REVIEW:
            raise PermissionError(
                "Security review requires vendor status SECURITY_REVIEW (NDA must be confirmed first)"
            )

        review.status = ReviewStatus.IN_PROGRESS
        db.commit()

        analyzer = SecurityAnalyzer(
            llm=LLMClient(),
            retriever=Retriever(store=VectorStore()),
        )

        try:
            result = await analyzer.analyze(review.vendor_id, doc_id)
            review.ai_output = result.to_dict()
            review.status = ReviewStatus.COMPLETE
            review.completed_at = datetime.utcnow()
            db.commit()

            self._log(
                vendor_id=review.vendor_id,
                event_type="SECURITY_REVIEW_COMPLETE",
                actor="system",
                payload={
                    "review_id": review_id,
                    "doc_id": doc_id,
                    "overall_risk": result.overall_risk,
                    "recommendation": result.recommendation,
                    "risk_score": result.risk_score,
                },
            )
            db.commit()

        except Exception as exc:
            logger.error(
                "Security review failed for review_id=%s doc_id=%s: %s",
                review_id,
                doc_id,
                exc,
            )
            review.status = ReviewStatus.ERROR
            review.completed_at = datetime.utcnow()
            db.commit()

            self._log(
                vendor_id=review.vendor_id,
                event_type="SECURITY_REVIEW_ERROR",
                actor="system",
                payload={
                    "review_id": review_id,
                    "doc_id": doc_id,
                    "error": str(exc),
                },
            )
            db.commit()

        db.refresh(review)
        return review

    def submit_security_decision(
        self,
        review_id: int,
        action: str,
        rationale: str,
        conditions: list | None = None,
        actor: str = "system",
    ) -> Vendor:
        """Record human decision on Stage 3 output; advance workflow state."""
        db = self.db

        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")
        if review.status != ReviewStatus.COMPLETE:
            raise ValueError("Review must be COMPLETE before a decision can be recorded")

        vendor = db.query(Vendor).filter(Vendor.id == review.vendor_id).first()
        if action in ("APPROVE", "APPROVE_WITH_CONDITIONS"):
            vendor.status = VendorStatus.SECURITY_APPROVED
            self._log(
                vendor_id=review.vendor_id,
                event_type="SECURITY_DECISION_APPROVED",
                actor=actor,
                payload={
                    "review_id": review_id,
                    "action": action,
                    "conditions": conditions or [],
                },
            )
        else:
            vendor.status = VendorStatus.REJECTED
            self._log(
                vendor_id=review.vendor_id,
                event_type="VENDOR_REJECTED",
                actor=actor,
                payload={
                    "review_id": review_id,
                    "stage": "SECURITY",
                    "action": action,
                    "rationale": rationale,
                },
            )
        db.commit()

        db.refresh(vendor)
        return vendor

    # ------------------------------------------------------------------
    # Stage 4 — Financial Risk Evaluation (human form)
    # ------------------------------------------------------------------

    def start_financial_review(self, vendor_id: int) -> tuple:
        """Open Stage 4 review for a vendor in SECURITY_APPROVED status."""
        db = self.db

        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise ValueError(f"Vendor {vendor_id} not found")
        if vendor.status != VendorStatus.SECURITY_APPROVED:
            raise ValueError(
                f"Vendor must be in SECURITY_APPROVED status, current: {vendor.status}"
            )

        review = Review(
            vendor_id=vendor_id,
            stage=DocumentStage.FINANCIAL,
            review_type=ReviewType.HUMAN_FORM,
            status=ReviewStatus.PENDING,
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        vendor.status = VendorStatus.FINANCIAL_REVIEW
        db.commit()

        self._log(
            vendor_id=vendor_id,
            event_type="FINANCIAL_REVIEW_STARTED",
            actor="system",
            payload={"vendor_id": vendor_id, "review_id": review.id},
        )
        db.commit()

        db.refresh(vendor)
        return (vendor, review)

    def submit_financial_form(self, review_id: int, form: FinancialRiskFormInput) -> Review:
        """Validate and store Stage 4 form; advance workflow on ACCEPTABLE."""
        db = self.db

        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise ValueError(f"Review {review_id} not found")

        review.form_input = form.model_dump()
        review.status = ReviewStatus.COMPLETE
        review.completed_at = datetime.utcnow()
        db.commit()

        vendor = db.query(Vendor).filter(Vendor.id == review.vendor_id).first()
        if form.recommendation in ("ACCEPTABLE", "ACCEPTABLE_WITH_CONDITIONS"):
            vendor.status = VendorStatus.FINANCIAL_APPROVED
            self._log(
                vendor_id=review.vendor_id,
                event_type="FINANCIAL_APPROVED",
                actor=form.reviewer_name,
                payload={
                    "review_id": review_id,
                    "conditions": form.conditions or [],
                },
            )
        else:
            vendor.status = VendorStatus.REJECTED
            self._log(
                vendor_id=review.vendor_id,
                event_type="VENDOR_REJECTED",
                actor=form.reviewer_name,
                payload={
                    "review_id": review_id,
                    "stage": "FINANCIAL",
                    "rationale": form.notes,
                },
            )
        db.commit()

        db.refresh(review)
        return review

    # ------------------------------------------------------------------
    # Final disposition
    # ------------------------------------------------------------------

    def complete_onboarding(self, vendor_id: int) -> Vendor:
        """Set vendor status to ONBOARDED after all stages approved."""
        db = self.db

        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise ValueError(f"Vendor {vendor_id} not found")
        if vendor.status != VendorStatus.FINANCIAL_APPROVED:
            raise ValueError(
                f"Vendor must be in FINANCIAL_APPROVED status, current: {vendor.status}"
            )

        vendor.status = VendorStatus.ONBOARDED
        self._log(
            vendor_id=vendor_id,
            event_type="ONBOARDING_COMPLETE",
            actor="system",
            payload={"vendor_id": vendor_id},
        )
        db.commit()
        db.refresh(vendor)
        return vendor

    def reject_vendor(self, vendor_id: int, stage: str, rationale: str) -> Vendor:
        """Reject vendor from any stage."""
        db = self.db

        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise ValueError(f"Vendor {vendor_id} not found")

        vendor.status = VendorStatus.REJECTED
        self._log(
            vendor_id=vendor_id,
            event_type="VENDOR_REJECTED",
            actor="system",
            payload={"vendor_id": vendor_id, "stage": stage, "rationale": rationale},
        )
        db.commit()
        db.refresh(vendor)
        return vendor

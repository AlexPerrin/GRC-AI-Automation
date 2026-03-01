"""
Unit tests for WorkflowService decision and financial/onboarding methods.
Uses db_session fixture directly — no LLM or ChromaDB involved.
"""
import pytest

from core.models import (
    AuditLog,
    DocumentStage,
    Review,
    ReviewStatus,
    ReviewType,
    Vendor,
    VendorStatus,
)
from schemas.forms import FinancialRiskFormInput
from services.workflow import WorkflowService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vendor(db, status=VendorStatus.LEGAL_REVIEW, name="Test Vendor"):
    v = Vendor(name=name, status=status)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def _make_complete_review(db, vendor_id, stage):
    r = Review(
        vendor_id=vendor_id,
        stage=stage,
        review_type=ReviewType.AI_ANALYSIS,
        status=ReviewStatus.COMPLETE,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _make_pending_review(db, vendor_id, stage):
    r = Review(
        vendor_id=vendor_id,
        stage=stage,
        review_type=ReviewType.AI_ANALYSIS,
        status=ReviewStatus.PENDING,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _financial_form(**kwargs) -> FinancialRiskFormInput:
    defaults = dict(
        financial_documents_reviewed=["balance_sheet"],
        concentration_risk_flag=False,
        financial_stability_assessment="STABLE",
        reviewer_name="Bob",
        recommendation="ACCEPTABLE",
        notes=None,
    )
    defaults.update(kwargs)
    return FinancialRiskFormInput(**defaults)


# ---------------------------------------------------------------------------
# TestSubmitLegalDecision
# ---------------------------------------------------------------------------

class TestSubmitLegalDecision:
    def test_approve_advances_vendor_to_legal_approved(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        r = _make_complete_review(db_session, v.id, DocumentStage.LEGAL)
        svc = WorkflowService(db_session)
        vendor = svc.submit_legal_decision(r.id, "APPROVE", "Looks good")
        assert vendor.status == VendorStatus.LEGAL_APPROVED

    def test_approve_with_conditions_advances_to_legal_approved(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        r = _make_complete_review(db_session, v.id, DocumentStage.LEGAL)
        svc = WorkflowService(db_session)
        vendor = svc.submit_legal_decision(
            r.id, "APPROVE_WITH_CONDITIONS", "With caveats", conditions=["Sign DPA"]
        )
        assert vendor.status == VendorStatus.LEGAL_APPROVED

    def test_reject_sets_vendor_to_rejected(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        r = _make_complete_review(db_session, v.id, DocumentStage.LEGAL)
        svc = WorkflowService(db_session)
        vendor = svc.submit_legal_decision(r.id, "REJECT", "Non-compliant")
        assert vendor.status == VendorStatus.REJECTED

    def test_approve_creates_legal_decision_approved_audit_log(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        r = _make_complete_review(db_session, v.id, DocumentStage.LEGAL)
        svc = WorkflowService(db_session)
        svc.submit_legal_decision(r.id, "APPROVE", "Looks good", actor="lawyer1")
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "LEGAL_DECISION_APPROVED",
        ).first()
        assert log is not None
        assert log.actor == "lawyer1"

    def test_reject_creates_vendor_rejected_audit_log(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        r = _make_complete_review(db_session, v.id, DocumentStage.LEGAL)
        svc = WorkflowService(db_session)
        svc.submit_legal_decision(r.id, "REJECT", "Bad policy")
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "VENDOR_REJECTED",
        ).first()
        assert log is not None
        assert log.payload["stage"] == "LEGAL"

    def test_raises_if_review_not_complete(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        r = _make_pending_review(db_session, v.id, DocumentStage.LEGAL)
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="COMPLETE"):
            svc.submit_legal_decision(r.id, "APPROVE", "ok")

    def test_raises_if_review_not_found(self, db_session):
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.submit_legal_decision(99999, "APPROVE", "ok")


# ---------------------------------------------------------------------------
# TestSubmitSecurityDecision
# ---------------------------------------------------------------------------

class TestSubmitSecurityDecision:
    def test_approve_advances_vendor_to_security_approved(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.SECURITY_REVIEW)
        r = _make_complete_review(db_session, v.id, DocumentStage.SECURITY)
        svc = WorkflowService(db_session)
        vendor = svc.submit_security_decision(r.id, "APPROVE", "Secure enough")
        assert vendor.status == VendorStatus.SECURITY_APPROVED

    def test_reject_sets_vendor_to_rejected(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.SECURITY_REVIEW)
        r = _make_complete_review(db_session, v.id, DocumentStage.SECURITY)
        svc = WorkflowService(db_session)
        vendor = svc.submit_security_decision(r.id, "REJECT", "Too risky")
        assert vendor.status == VendorStatus.REJECTED

    def test_approve_creates_security_decision_approved_audit_log(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.SECURITY_REVIEW)
        r = _make_complete_review(db_session, v.id, DocumentStage.SECURITY)
        svc = WorkflowService(db_session)
        svc.submit_security_decision(r.id, "APPROVE", "ok", actor="sec_team")
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "SECURITY_DECISION_APPROVED",
        ).first()
        assert log is not None
        assert log.actor == "sec_team"

    def test_raises_if_review_not_complete(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.SECURITY_REVIEW)
        r = _make_pending_review(db_session, v.id, DocumentStage.SECURITY)
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="COMPLETE"):
            svc.submit_security_decision(r.id, "APPROVE", "ok")

    def test_raises_if_review_not_found(self, db_session):
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.submit_security_decision(99999, "APPROVE", "ok")


# ---------------------------------------------------------------------------
# TestSubmitFinancialForm
# ---------------------------------------------------------------------------

class TestSubmitFinancialForm:
    def _setup(self, db_session, rec="ACCEPTABLE"):
        v = _make_vendor(db_session, status=VendorStatus.FINANCIAL_REVIEW)
        r = Review(
            vendor_id=v.id,
            stage=DocumentStage.FINANCIAL,
            review_type=ReviewType.HUMAN_FORM,
            status=ReviewStatus.PENDING,
        )
        db_session.add(r)
        db_session.commit()
        db_session.refresh(r)
        return v, r

    def test_acceptable_advances_to_financial_approved(self, db_session):
        v, r = self._setup(db_session)
        svc = WorkflowService(db_session)
        svc.submit_financial_form(r.id, _financial_form(recommendation="ACCEPTABLE"))
        db_session.refresh(v)
        assert v.status == VendorStatus.FINANCIAL_APPROVED

    def test_acceptable_with_conditions_advances_to_financial_approved(self, db_session):
        v, r = self._setup(db_session)
        svc = WorkflowService(db_session)
        svc.submit_financial_form(
            r.id,
            _financial_form(recommendation="ACCEPTABLE_WITH_CONDITIONS", conditions=["Pay upfront"]),
        )
        db_session.refresh(v)
        assert v.status == VendorStatus.FINANCIAL_APPROVED

    def test_unacceptable_sets_vendor_rejected(self, db_session):
        v, r = self._setup(db_session)
        svc = WorkflowService(db_session)
        svc.submit_financial_form(r.id, _financial_form(recommendation="UNACCEPTABLE"))
        db_session.refresh(v)
        assert v.status == VendorStatus.REJECTED

    def test_review_status_set_to_complete(self, db_session):
        _v, r = self._setup(db_session)
        svc = WorkflowService(db_session)
        result = svc.submit_financial_form(r.id, _financial_form())
        assert result.status == ReviewStatus.COMPLETE

    def test_form_input_stored_and_completed_at_set(self, db_session):
        _v, r = self._setup(db_session)
        svc = WorkflowService(db_session)
        result = svc.submit_financial_form(r.id, _financial_form(reviewer_name="Carol"))
        assert result.form_input["reviewer_name"] == "Carol"
        assert result.completed_at is not None

    def test_acceptable_creates_financial_approved_audit_log(self, db_session):
        v, r = self._setup(db_session)
        svc = WorkflowService(db_session)
        svc.submit_financial_form(r.id, _financial_form(recommendation="ACCEPTABLE"))
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "FINANCIAL_APPROVED",
        ).first()
        assert log is not None

    def test_unacceptable_creates_vendor_rejected_audit_log(self, db_session):
        v, r = self._setup(db_session)
        svc = WorkflowService(db_session)
        svc.submit_financial_form(r.id, _financial_form(recommendation="UNACCEPTABLE"))
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "VENDOR_REJECTED",
        ).first()
        assert log is not None
        assert log.payload["stage"] == "FINANCIAL"


# ---------------------------------------------------------------------------
# TestCompleteOnboarding
# ---------------------------------------------------------------------------

class TestCompleteOnboarding:
    def test_financial_approved_advances_to_onboarded(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.FINANCIAL_APPROVED)
        svc = WorkflowService(db_session)
        vendor = svc.complete_onboarding(v.id)
        assert vendor.status == VendorStatus.ONBOARDED

    def test_creates_onboarding_complete_audit_log(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.FINANCIAL_APPROVED)
        svc = WorkflowService(db_session)
        svc.complete_onboarding(v.id)
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "ONBOARDING_COMPLETE",
        ).first()
        assert log is not None
        assert log.actor == "system"

    def test_raises_if_not_financial_approved(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.SECURITY_APPROVED)
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="FINANCIAL_APPROVED"):
            svc.complete_onboarding(v.id)

    def test_raises_if_vendor_not_found(self, db_session):
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.complete_onboarding(99999)


# ---------------------------------------------------------------------------
# TestRejectVendor
# ---------------------------------------------------------------------------

class TestRejectVendor:
    def test_rejects_vendor_from_any_status(self, db_session):
        for status in (
            VendorStatus.INTAKE,
            VendorStatus.LEGAL_REVIEW,
            VendorStatus.SECURITY_APPROVED,
        ):
            v = _make_vendor(db_session, status=status, name=f"Vendor-{status}")
            svc = WorkflowService(db_session)
            vendor = svc.reject_vendor(v.id, stage=status.value, rationale="Test")
            assert vendor.status == VendorStatus.REJECTED

    def test_creates_vendor_rejected_audit_log_with_stage_and_rationale(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        svc = WorkflowService(db_session)
        svc.reject_vendor(v.id, stage="LEGAL", rationale="Policy violation")
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "VENDOR_REJECTED",
        ).first()
        assert log is not None
        assert log.payload["stage"] == "LEGAL"
        assert log.payload["rationale"] == "Policy violation"

    def test_raises_if_vendor_not_found(self, db_session):
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.reject_vendor(99999, stage="MANUAL", rationale="Gone")

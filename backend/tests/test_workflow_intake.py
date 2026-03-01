"""
Unit tests for WorkflowService intake and use-case-form methods.
Uses db_session fixture directly — no LLM or ChromaDB involved.
"""
import pytest

from core.models import AuditLog, DocumentStage, Review, ReviewStatus, ReviewType, Vendor, VendorStatus
from schemas.forms import UseCaseFormInput
from services.workflow import WorkflowService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vendor(db, status=VendorStatus.INTAKE, name="Test Vendor"):
    v = Vendor(name=name, status=status)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def _use_case_form(**kwargs) -> UseCaseFormInput:
    defaults = dict(
        use_case_description="Automate procurement",
        business_justification="Saves 20 hrs/week",
        data_types_involved=["PII", "contracts"],
        estimated_users=50,
        alternatives_considered="Manual process",
        reviewer_name="Alice",
        recommendation="PROCEED",
        notes=None,
    )
    defaults.update(kwargs)
    return UseCaseFormInput(**defaults)


# ---------------------------------------------------------------------------
# TestCreateVendorAndIntake
# ---------------------------------------------------------------------------

class TestCreateVendorAndIntake:
    def test_returns_vendor_and_review_tuple(self, db_session):
        v = _make_vendor(db_session)
        svc = WorkflowService(db_session)
        vendor, review = svc.create_vendor_and_intake(v.id)
        assert isinstance(vendor, Vendor)
        assert isinstance(review, Review)

    def test_creates_use_case_review(self, db_session):
        v = _make_vendor(db_session)
        svc = WorkflowService(db_session)
        _vendor, review = svc.create_vendor_and_intake(v.id)
        assert review.stage == DocumentStage.USE_CASE
        assert review.review_type == ReviewType.HUMAN_FORM
        assert review.status == ReviewStatus.PENDING
        assert review.vendor_id == v.id

    def test_vendor_status_advances_to_use_case_review(self, db_session):
        v = _make_vendor(db_session)
        svc = WorkflowService(db_session)
        vendor, _review = svc.create_vendor_and_intake(v.id)
        assert vendor.status == VendorStatus.USE_CASE_REVIEW

    def test_audit_log_intake_started_created(self, db_session):
        v = _make_vendor(db_session)
        svc = WorkflowService(db_session)
        svc.create_vendor_and_intake(v.id)
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "INTAKE_STARTED",
        ).first()
        assert log is not None
        assert log.actor == "system"

    def test_raises_if_vendor_not_found(self, db_session):
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.create_vendor_and_intake(99999)

    def test_raises_if_vendor_not_in_intake_status(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="INTAKE"):
            svc.create_vendor_and_intake(v.id)


# ---------------------------------------------------------------------------
# TestSubmitUseCaseForm
# ---------------------------------------------------------------------------

class TestSubmitUseCaseForm:
    def _setup(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.USE_CASE_REVIEW)
        review = Review(
            vendor_id=v.id,
            stage=DocumentStage.USE_CASE,
            review_type=ReviewType.HUMAN_FORM,
            status=ReviewStatus.PENDING,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        return v, review

    def test_proceed_advances_vendor_to_use_case_approved(self, db_session):
        v, review = self._setup(db_session)
        svc = WorkflowService(db_session)
        svc.submit_use_case_form(review.id, _use_case_form(recommendation="PROCEED"))
        db_session.refresh(v)
        assert v.status == VendorStatus.USE_CASE_APPROVED

    def test_do_not_proceed_sets_vendor_rejected(self, db_session):
        v, review = self._setup(db_session)
        svc = WorkflowService(db_session)
        svc.submit_use_case_form(review.id, _use_case_form(recommendation="DO_NOT_PROCEED"))
        db_session.refresh(v)
        assert v.status == VendorStatus.REJECTED

    def test_review_status_set_to_complete(self, db_session):
        _v, review = self._setup(db_session)
        svc = WorkflowService(db_session)
        result = svc.submit_use_case_form(review.id, _use_case_form())
        assert result.status == ReviewStatus.COMPLETE

    def test_form_input_stored_on_review(self, db_session):
        _v, review = self._setup(db_session)
        svc = WorkflowService(db_session)
        form = _use_case_form(notes="Looks good")
        result = svc.submit_use_case_form(review.id, form)
        assert result.form_input is not None
        assert result.form_input["notes"] == "Looks good"

    def test_completed_at_set(self, db_session):
        _v, review = self._setup(db_session)
        svc = WorkflowService(db_session)
        result = svc.submit_use_case_form(review.id, _use_case_form())
        assert result.completed_at is not None

    def test_proceed_creates_use_case_approved_audit_log(self, db_session):
        v, review = self._setup(db_session)
        svc = WorkflowService(db_session)
        svc.submit_use_case_form(review.id, _use_case_form(recommendation="PROCEED"))
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "USE_CASE_APPROVED",
        ).first()
        assert log is not None

    def test_do_not_proceed_creates_vendor_rejected_audit_log(self, db_session):
        v, review = self._setup(db_session)
        svc = WorkflowService(db_session)
        svc.submit_use_case_form(review.id, _use_case_form(recommendation="DO_NOT_PROCEED"))
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "VENDOR_REJECTED",
        ).first()
        assert log is not None
        assert log.payload["stage"] == "USE_CASE"


# ---------------------------------------------------------------------------
# TestStartFinancialReview
# ---------------------------------------------------------------------------

class TestStartFinancialReview:
    def test_creates_financial_review_and_advances_vendor(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.SECURITY_APPROVED)
        svc = WorkflowService(db_session)
        vendor, review = svc.start_financial_review(v.id)
        assert vendor.status == VendorStatus.FINANCIAL_REVIEW
        assert review.stage == DocumentStage.FINANCIAL
        assert review.review_type == ReviewType.HUMAN_FORM
        assert review.status == ReviewStatus.PENDING

    def test_audit_log_financial_review_started(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.SECURITY_APPROVED)
        svc = WorkflowService(db_session)
        svc.start_financial_review(v.id)
        log = db_session.query(AuditLog).filter(
            AuditLog.vendor_id == v.id,
            AuditLog.event_type == "FINANCIAL_REVIEW_STARTED",
        ).first()
        assert log is not None
        assert log.actor == "system"

    def test_raises_if_vendor_not_security_approved(self, db_session):
        v = _make_vendor(db_session, status=VendorStatus.LEGAL_APPROVED)
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="SECURITY_APPROVED"):
            svc.start_financial_review(v.id)

    def test_raises_if_vendor_not_found(self, db_session):
        svc = WorkflowService(db_session)
        with pytest.raises(ValueError, match="not found"):
            svc.start_financial_review(99999)

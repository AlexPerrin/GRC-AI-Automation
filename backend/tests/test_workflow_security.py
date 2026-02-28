"""
Integration tests for WorkflowService.confirm_nda and trigger_security_review (Day 4).

Uses the db_session fixture (in-memory SQLite) from conftest.py.
SecurityAnalyzer.analyze is patched as an AsyncMock so no real LLM or ChromaDB
calls are made.
"""
import pytest
from unittest.mock import AsyncMock, patch

from core.models import (
    AuditLog,
    DocumentStage,
    Review,
    ReviewStatus,
    ReviewType,
    Vendor,
    VendorStatus,
)
from services.security.analyzer import ControlFinding, SecurityAnalysisResult
from services.workflow import WorkflowService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vendor(db_session):
    v = Vendor(name="ACME Corp", status=VendorStatus.LEGAL_APPROVED)
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v


@pytest.fixture
def security_review(db_session, vendor):
    # Vendor must be SECURITY_REVIEW for the analysis gate
    vendor.status = VendorStatus.SECURITY_REVIEW
    db_session.commit()
    r = Review(
        vendor_id=vendor.id,
        stage=DocumentStage.SECURITY,
        review_type=ReviewType.AI_ANALYSIS,
        status=ReviewStatus.PENDING,
    )
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


def _make_analysis_result(overall_risk: str = "medium", recommendation: str = "approve_with_conditions"):
    return SecurityAnalysisResult(
        control_findings=[
            ControlFinding(
                domain="access_control",
                framework="NIST CSF",
                control_id="PR.AC",
                status="partial",
                finding="MFA enforced for privileged accounts but not all remote access.",
                evidence="Vendor states MFA is required for admin accounts.",
                risk_score=2,
            )
        ],
        overall_risk=overall_risk,  # type: ignore[arg-type]
        recommendation=recommendation,  # type: ignore[arg-type]
        summary="Vendor has adequate controls with some gaps in access management.",
        conditions=["Enable MFA for all remote access connections"],
        risk_score=2.0,
    )


# ---------------------------------------------------------------------------
# confirm_nda tests
# ---------------------------------------------------------------------------

class TestConfirmNda:
    def test_advances_vendor_status_to_security_review(self, db_session, vendor):
        assert vendor.status == VendorStatus.LEGAL_APPROVED
        svc = WorkflowService(db=db_session)
        returned = svc.confirm_nda(vendor.id)
        assert returned.status == VendorStatus.SECURITY_REVIEW

    def test_audit_log_nda_confirmed_created(self, db_session, vendor):
        WorkflowService(db=db_session).confirm_nda(vendor.id)
        log = (
            db_session.query(AuditLog)
            .filter(AuditLog.event_type == "NDA_CONFIRMED")
            .first()
        )
        assert log is not None
        assert log.vendor_id == vendor.id

    def test_raises_for_wrong_status(self, db_session):
        v = Vendor(name="Wrong Status Vendor", status=VendorStatus.INTAKE)
        db_session.add(v)
        db_session.commit()
        with pytest.raises(ValueError, match="LEGAL_APPROVED"):
            WorkflowService(db=db_session).confirm_nda(v.id)

    def test_raises_for_missing_vendor(self, db_session):
        with pytest.raises(ValueError, match="not found"):
            WorkflowService(db=db_session).confirm_nda(99999)


# ---------------------------------------------------------------------------
# trigger_security_review tests
# ---------------------------------------------------------------------------

class TestTriggerSecurityReviewSuccess:
    async def test_review_status_set_to_complete(self, db_session, vendor, security_review):
        mock_result = _make_analysis_result()
        with patch(
            "services.workflow.SecurityAnalyzer.analyze",
            new=AsyncMock(return_value=mock_result),
        ):
            returned = await WorkflowService(db=db_session).trigger_security_review(
                security_review.id, doc_id=1
            )
        assert returned.status == ReviewStatus.COMPLETE

    async def test_ai_output_populated(self, db_session, vendor, security_review):
        mock_result = _make_analysis_result(overall_risk="high", recommendation="approve_with_conditions")
        with patch(
            "services.workflow.SecurityAnalyzer.analyze",
            new=AsyncMock(return_value=mock_result),
        ):
            returned = await WorkflowService(db=db_session).trigger_security_review(
                security_review.id, doc_id=1
            )
        assert returned.ai_output["overall_risk"] == "high"
        assert returned.ai_output["risk_score"] == 2.0

    async def test_completed_at_set(self, db_session, vendor, security_review):
        mock_result = _make_analysis_result()
        with patch(
            "services.workflow.SecurityAnalyzer.analyze",
            new=AsyncMock(return_value=mock_result),
        ):
            returned = await WorkflowService(db=db_session).trigger_security_review(
                security_review.id, doc_id=1
            )
        assert returned.completed_at is not None

    async def test_audit_log_complete_event(self, db_session, vendor, security_review):
        mock_result = _make_analysis_result()
        with patch(
            "services.workflow.SecurityAnalyzer.analyze",
            new=AsyncMock(return_value=mock_result),
        ):
            await WorkflowService(db=db_session).trigger_security_review(
                security_review.id, doc_id=1
            )
        log = (
            db_session.query(AuditLog)
            .filter(AuditLog.event_type == "SECURITY_REVIEW_COMPLETE")
            .first()
        )
        assert log is not None
        assert log.vendor_id == vendor.id


class TestTriggerSecurityReviewError:
    async def test_review_status_set_to_error_on_exception(
        self, db_session, vendor, security_review
    ):
        with patch(
            "services.workflow.SecurityAnalyzer.analyze",
            new=AsyncMock(side_effect=RuntimeError("LLM unavailable")),
        ):
            returned = await WorkflowService(db=db_session).trigger_security_review(
                security_review.id, doc_id=1
            )
        assert returned.status == ReviewStatus.ERROR

    async def test_audit_log_error_event(self, db_session, vendor, security_review):
        with patch(
            "services.workflow.SecurityAnalyzer.analyze",
            new=AsyncMock(side_effect=RuntimeError("LLM unavailable")),
        ):
            await WorkflowService(db=db_session).trigger_security_review(
                security_review.id, doc_id=1
            )
        log = (
            db_session.query(AuditLog)
            .filter(AuditLog.event_type == "SECURITY_REVIEW_ERROR")
            .first()
        )
        assert log is not None
        assert "error" in log.payload


class TestNdaGate:
    async def test_trigger_security_review_raises_permission_error_if_not_security_review(
        self, db_session
    ):
        """Vendor in LEGAL_APPROVED (NDA not yet confirmed) should raise PermissionError."""
        v = Vendor(name="Gate Test Vendor", status=VendorStatus.LEGAL_APPROVED)
        db_session.add(v)
        db_session.commit()
        r = Review(
            vendor_id=v.id,
            stage=DocumentStage.SECURITY,
            review_type=ReviewType.AI_ANALYSIS,
            status=ReviewStatus.PENDING,
        )
        db_session.add(r)
        db_session.commit()

        with pytest.raises(PermissionError, match="NDA must be confirmed"):
            await WorkflowService(db=db_session).trigger_security_review(r.id, doc_id=1)

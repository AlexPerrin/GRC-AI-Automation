"""
Integration tests for WorkflowService.trigger_legal_review (Day 3).

Uses the db_session fixture (in-memory SQLite) from conftest.py.
LegalAnalyzer.analyze is patched as an AsyncMock so no real LLM or ChromaDB
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
from services.legal.analyzer import LegalAnalysisResult, RegulationFinding
from services.workflow import WorkflowService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vendor(db_session):
    v = Vendor(
        name="ACME Corp",
        website="https://acme.example.com",
        status=VendorStatus.USE_CASE_APPROVED,
    )
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v


@pytest.fixture
def legal_review(db_session, vendor):
    r = Review(
        vendor_id=vendor.id,
        stage=DocumentStage.LEGAL,
        review_type=ReviewType.AI_ANALYSIS,
        status=ReviewStatus.PENDING,
    )
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


def _make_analysis_result(overall_risk: str = "low", recommendation: str = "approve"):
    return LegalAnalysisResult(
        regulation_findings=[
            RegulationFinding(
                regulation="GDPR",
                article="Art. 5",
                status="compliant",
                finding="Data processing is lawful.",
                evidence="Vendor states lawful basis in section 2.",
            )
        ],
        overall_risk=overall_risk,  # type: ignore[arg-type]
        recommendation=recommendation,  # type: ignore[arg-type]
        summary="Overall vendor demonstrates adequate compliance.",
        conditions=[],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTriggerLegalReviewSuccess:
    async def test_review_status_set_to_complete(self, db_session, vendor, legal_review):
        mock_result = _make_analysis_result()
        with patch(
            "services.workflow.LegalAnalyzer.analyze",
            new=AsyncMock(return_value=mock_result),
        ):
            svc = WorkflowService(db=db_session)
            returned = await svc.trigger_legal_review(legal_review.id, doc_id=1)

        assert returned.status == ReviewStatus.COMPLETE

    async def test_ai_output_populated_with_risk_and_recommendation(
        self, db_session, vendor, legal_review
    ):
        mock_result = _make_analysis_result(overall_risk="medium", recommendation="approve_with_conditions")
        with patch(
            "services.workflow.LegalAnalyzer.analyze",
            new=AsyncMock(return_value=mock_result),
        ):
            svc = WorkflowService(db=db_session)
            returned = await svc.trigger_legal_review(legal_review.id, doc_id=1)

        assert returned.ai_output is not None
        assert returned.ai_output["overall_risk"] == "medium"
        assert returned.ai_output["recommendation"] == "approve_with_conditions"

    async def test_completed_at_set(self, db_session, vendor, legal_review):
        mock_result = _make_analysis_result()
        with patch(
            "services.workflow.LegalAnalyzer.analyze",
            new=AsyncMock(return_value=mock_result),
        ):
            svc = WorkflowService(db=db_session)
            returned = await svc.trigger_legal_review(legal_review.id, doc_id=1)

        assert returned.completed_at is not None

    async def test_audit_log_created_with_complete_event(
        self, db_session, vendor, legal_review
    ):
        mock_result = _make_analysis_result()
        with patch(
            "services.workflow.LegalAnalyzer.analyze",
            new=AsyncMock(return_value=mock_result),
        ):
            svc = WorkflowService(db=db_session)
            await svc.trigger_legal_review(legal_review.id, doc_id=1)

        log = (
            db_session.query(AuditLog)
            .filter(AuditLog.event_type == "LEGAL_REVIEW_COMPLETE")
            .first()
        )
        assert log is not None
        assert log.vendor_id == vendor.id

    async def test_vendor_status_set_to_legal_review(
        self, db_session, vendor, legal_review
    ):
        mock_result = _make_analysis_result()
        with patch(
            "services.workflow.LegalAnalyzer.analyze",
            new=AsyncMock(return_value=mock_result),
        ):
            svc = WorkflowService(db=db_session)
            await svc.trigger_legal_review(legal_review.id, doc_id=1)

        db_session.refresh(vendor)
        assert vendor.status == VendorStatus.LEGAL_REVIEW


class TestTriggerLegalReviewError:
    async def test_review_status_set_to_error_on_exception(
        self, db_session, vendor, legal_review
    ):
        with patch(
            "services.workflow.LegalAnalyzer.analyze",
            new=AsyncMock(side_effect=RuntimeError("LLM unavailable")),
        ):
            svc = WorkflowService(db=db_session)
            returned = await svc.trigger_legal_review(legal_review.id, doc_id=1)

        assert returned.status == ReviewStatus.ERROR

    async def test_audit_log_created_with_error_event(
        self, db_session, vendor, legal_review
    ):
        with patch(
            "services.workflow.LegalAnalyzer.analyze",
            new=AsyncMock(side_effect=RuntimeError("LLM unavailable")),
        ):
            svc = WorkflowService(db=db_session)
            await svc.trigger_legal_review(legal_review.id, doc_id=1)

        log = (
            db_session.query(AuditLog)
            .filter(AuditLog.event_type == "LEGAL_REVIEW_ERROR")
            .first()
        )
        assert log is not None
        assert "error" in log.payload
